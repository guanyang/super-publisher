# 微信表情制作

从明确布局的透明网格导出居中PNG，或通过一份pack.json完成整包生产。生图、角色与文案内容由Agent负责，脚本负责可重复的图片加工。

```bash
# 单独切片，必须明确布局
python3 skills/wechat-sticker-maker/scripts/make_stickers.py grid.png --layout 4x4 --output output/slices_v1
# 带字16宫格预览（不生成配套图或ZIP）
python3 skills/wechat-sticker-maker/scripts/build_pack.py --spec pack.json --output output/preview_v1 --preview-only
# 补齐配套素材后的完整交付
python3 skills/wechat-sticker-maker/scripts/build_pack.py --spec pack.json --output output/complete_v1
```

配置、模式和目录见[技能说明](SKILL.md)与[pack.json字段](references/pack-spec.md)，带字设计见[排版参考](references/typography.md)。完整打包需同仓库的wechat-sticker-assets-designer；脚本可直接从源码目录或技能软链接运行。安装依赖使用`python3 -m pip install -r skills/wechat-sticker-maker/requirements.txt`。

render支持整套默认样式、逐张覆盖、字体角色与TTC索引、小字号、上置/下置/轻弧形和轻微倾斜。旧font配置仍可使用；只改文字时复用无字源图。追加`--compare-typography`可生成A/B对照图，实际字体和布局记录于manifest.json；普通构建不强制试排。

支持真实透明检测、透明间隙切片、明确边界、等比居中、程序排字、240主图、120缩略图、50小图、无字封面与聊天图标、配图尺寸与压缩、预览、元数据、检查清单、保留源图及ZIP。存在旧输出时拒绝覆盖，重跑使用新的版本目录。

不要根据图片长宽比猜九宫格或十六宫格；找不到安全间隙要停下检查。白底转RGBA不等于去底。仅尺寸、透明与文件检查通过，不代表画面、文字或平台审核已通过。

测试：`python3 -m unittest discover -s skills/wechat-sticker-maker/tests -v`。
