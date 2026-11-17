---
name: wechat-sticker-maker
description: 将明确布局的透明网格切成居中PNG，或使用pack.json完成文案排版、主图缩略图、配套图处理、检查预览和ZIP打包。支持只出预览，拒绝覆盖已有成品。
---

# 微信表情制作

需要Python 3.9+、Pillow。本地尺寸和体积目标不代表平台已审核；本技能不登录或提交微信。

## 只切图

```bash
python3 <skill-dir>/scripts/make_stickers.py grid.png --layout 4x4 --output output/new_version
```

必须明确行数x列数，不根据长宽比猜宫格数量。默认校验真实透明；只有用户明确要求保留不透明背景时才传`--allow-opaque`。

分隔线在预期位置附近寻找连续透明间隙，以alpha>24为可见内容阈值。找不到间隙就停止，不能静默切断内容。检查图片后可用`--boundaries cuts.json`明确指定x/y像素边界，边界仍不可穿过可见内容。

输出main/240×240、thumbnail/120×120、icon/50×50、original_slices/、原图、cuts.json及元数据模板。图片等比缩放并居中，主图留12像素空白；icon/只是逐张小图，不是专辑聊天图标。模板未填不能称为完整素材包。

## 从一份配置生成完整素材

配置与可复制示例见[pack.json说明](references/pack-spec.md)。整包入口目前面向16张4x4静态PNG，不将16种独立表情转成GIF动画。

```bash
# 只看16宫格：不处理配套图，不生成ZIP
python3 <skill-dir>/scripts/build_pack.py --spec pack.json --output output/preview_v1 --preview-only
# 用户确认后，补齐配置中的配套原图，导出新版本
python3 <skill-dir>/scripts/build_pack.py --spec pack.json --output output/complete_v1
```

- 完整打包需同时安装同仓库的wechat-sticker-assets-designer；脚本复用其图片处理逻辑。
- caption_mode：baked保留图中文字，render从无字图程序排字，none输出无字；三种模式都从items生成同一份meta.txt。
- render可用旧font或fonts角色映射指定本机字体与TTC索引；整套typography可由逐张配置覆盖。需要带字设计或比较排版时读取[排版参考](references/typography.md)，先保证角色主导，再用小文字与少量变化辅助情绪。
- 默认23px为试排起点，可调整字体、字重、大小、配色、描边及下置、上置、轻弧形布局；组合只平移居中，不整体放大。缺字或文案无法清晰排下时停止，不静默换字体或丢字；字体文件不随素材包分发。
- 需要A/B试排时增加--compare-typography，输出统一默认字体下置版与逐张配置版对照；普通构建不强制增加比较或确认环节。
- 封面、聊天图标使用明确指定的无字source，可附crop坐标。不自动将第一张带字主图当作成品封面和图标。
- 完整包默认需cover、chat_icon、banner、reward_guide及reward_thanks；赞赏引导图与致谢图是默认交付项。仅用户明确不要赞赏配图时，设置include_rewards=false并成对省略；不能因未提赞赏或未开通赞赏功能而省略。场景配图用有色不透明背景，角色主图、封面、图标用真实透明PNG。
- 输出目录或同名ZIP存在就停止，保留用户元数据及成品；重跑使用新版本路径。构建、校验在临时目录完成，失败不留下假成功目录。

## 交付检查

自动检查编号、数量、PNG尺寸、透明像素、可见内容留白、文件大小、配套图及ZIP完整性。生成浅深背景preview.png、透明总览grid.png、manifest.json、info.txt、meta.txt和保留原图的source/。

本地目标：主图240×240且≤100KiB，缩略图120×120且≤50KiB，小图50×50且≤30KiB；封面240×240且≤80KiB，聊天图标50×50且≤30KiB，横幅750×400、赞赏引导750×560、致谢750×750且各≤500KiB。这些是生产约定，平台规则以实际提交页为准。

交付前必须视觉检查单张实际尺寸与整套预览：角色一致、文案准确、顺序正确、无跨格残留、尾巴道具完整，文字辅助表情且整套协调。脚本透明检测不能判断文字对错或字体与情绪是否匹配，也不能保证视觉美观。说明静态或动态，给ZIP和预览的绝对链接；不称作已上架或已通过审核。
