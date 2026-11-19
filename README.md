# Super Publisher

Super Publisher 是一个专为 Agent 设计的插件，旨在实现自动化的多平台内容发布。

版本更新记录请查看 [更新日志（CHANGELOG）](CHANGELOG.md)。

## 🌟 核心功能

### Toutiao Publisher (`skills/toutiao-publisher`)
> 架构原理及最佳实践请参考[skills/toutiao-publisher](skills/toutiao-publisher/README.md)。
- **持久化登录**：一次扫码，长期有效，自动管理 Session。
- **自动化发布**：通过命令行或自然语言指令自动发布文章。
- **智能适配**：自动优化标题长度，支持 Markdown 转 HTML。
- **无头模式**：支持后台静默运行。

### WeChat Post Publisher (`skills/wechat-post-publisher`)
> 详细文档及配置说明请参考 [skills/wechat-post-publisher/README.md](skills/wechat-post-publisher/README.md)。
- **全栈式大模型发文引擎**：提供将创作出的本地 Markdown 文档即时转化为微信公众号富文本底稿的能力。
- **自动化图片与外链洗练**：自动接管网络引文并降级为文尾学术标注；并支持自动上传处理本地的配图文件上微信 CDN 素材库。
- **多租户极客沙盒 (Multi-tenant)**：原生内置了凭据分离墙，利用 `--account` 一键切分并加载多重维度的测试或商业公号资源池。

### WeChat Red Packet Designer (`skills/wechat-red-packet-designer`)
> 从主题、参考角色或现成画稿制作静态微信红包封面。见[技能说明](skills/wechat-red-packet-designer/SKILL.md)。
- [风格目录与图库](skills/wechat-red-packet-designer/references/styles.md)包含 5 组九宫格和 45 个创意样张，供未指定风格时参考。
- 支持焦点裁切和独立版本导出，复用同一画稿进行构图修改。
- 可选导出静态[封面挂件和气泡挂件](skills/wechat-red-packet-designer/references/charms.md)，按官方模板检查透明避让区。
- 需要整包时可[从所选预览打包](skills/wechat-red-packet-designer/references/export.md)，上传素材原样入包。
- 用实际 JPEG 同时检查完整画面、遮挡和小尺寸效果，按需交付预览或上传用素材。

### WeChat Sticker Maker (`skills/wechat-sticker-maker`)
> 详细文档请参考 [skills/wechat-sticker-maker/README.md](skills/wechat-sticker-maker/README.md)。
- **可靠切分**：明确布局并寻找透明间隙，拒绝穿过可见内容；默认真实透明PNG、等比居中和安全留白。
- **整包加工**：从一份 `pack.json` 导出240主图、120缩略图、50小图、配图、文案、预览、检查清单和ZIP。
- **独立排字与安全重跑**：支持情绪字体、逐张排版与A/B对照，或保留已有文案；保留原图，拒绝覆盖既有成品和元数据。

### WeChat Sticker Assets Designer (`skills/wechat-sticker-assets-designer`)
> 详细文档请参考 [skills/wechat-sticker-assets-designer/README.md](skills/wechat-sticker-assets-designer/README.md)。
- **规范化生成**：根据用户提供的表情包 IP 形象，一键生成符合微信表情官方规范的横幅 (Banner, 750x400)、赞赏引导图 (750x560) 和赞赏致谢图 (750x750)。
- **条件化裁剪**：内置 Pillow 条件裁剪与缩放脚本，确保导出的图稿像素和构图精准无误。
- **继承角色画风**：支持立体毛发、手绘、矢量等参考风格，整包默认包含赞赏引导图及致谢图，仅用户明确不要时成对省略；示例文案可替换，尺寸加工保留原图。

### Grid Sticker Generator (`skills/grid-sticker-generator`)
> 详细文档请参考 [skills/grid-sticker-generator/README.md](skills/grid-sticker-generator/README.md)。
- **通用生成**：按已确认画风生成居中留白的4x4透明网格，支持带字或无字，不强制扁平矢量。
- **模板支持**：内置“打工人”模板，支持加载不同主题的梗库和动作列表。

### Sticker Factory (`skills/sticker-factory`)
> 详细文档请参考 [skills/sticker-factory/README.md](skills/sticker-factory/README.md)。
- **全流程编排**：作为“工厂经理”，串联网格生成器、表情包切片制作器及配套宣传素材设计器。
- **一键整合交付**：从自然语言需求（如 "生成一套快乐小狗表情包"）直接产出包含表情包切片、图标、元数据以及裁剪好的配套 Banner 与赞赏致谢图的一体化输出目录。

### Animated Sticker Maker (`skills/animated-sticker-maker`)
> 从照片、静态角色或动作点子设计循环表情，流程见[动态表情制作](skills/animated-sticker-maker/SKILL.md)。
- [画风与主题参考](skills/animated-sticker-maker/references/creative-directions.md)供按需选择或组合。
- 按要求交付小样或整套，收到修改意见时可复用其他条目。批量入口读取清单，一次导出 GIF、审片页及可选 ZIP。
- 审片页打开即可看到代表姿势，可切换到实际 GIF 播放并比较深浅背景。批量入口使用同仓库的 GIF 编码组件。

### GIF Maker (`skills/gif-maker`)
> 详细文档请参考 [skills/gif-maker/README.md](skills/gif-maker/README.md)。
- **连续帧加工**：支持透明安全切分、自然排序、共享调色板与公共构图，保留动作真实位移。
- **节奏与复核**：支持帧顺序、逐帧时长及静态文案层，输出解码预览和制作记录，永久循环。
- **可靠导出**：按显式体积目标压缩，保持尺寸与时间线；校验通过后发布成品，支持可选无损优化。

### Video Tutorial Maker (`skills/video-tutorial-maker`)
- **教程视频生成**：将主题、提纲、脚本或既有视频整理成带旁白的教程视频包。
- **音画字幕同步**：按场景生成 TTS、时间线字幕与固定时长视频片段，避免多段拼接后的字幕或语音漂移。
- **平台版本适配**：默认输出 1920x1080 横屏 MP4，并在需要时指导生成 9:16 等平台变体。

### Excalidraw Visual Designer (`skills/excalidraw-visual-designer`)
- **可编辑视觉设计**：通过 Excalidraw 创建或修改可编辑的图表、流程图、架构草图、信息图和海报版式。
- **剪贴板 JSON 导入**：内置通用生成脚本，可将场景规格转换为 Excalidraw clipboard JSON，减少复杂布局的手工拖拽。
- **连线与版面质量控制**：强调连线绕行、标签可读性、视觉层级和截图复查，降低箭头穿插和文字重叠问题。

## 📂 项目结构

```
.
├── .claude-plugin/      # Claude 插件配置文件
├── skills/              # Agent Skills 目录
│   ├── animated-sticker-maker/ # 动态表情动作创作与审片 Skill
│   ├── excalidraw-visual-designer/ # Excalidraw 可编辑视觉设计 Skill
│   ├── gif-maker/            # [NEW] GIF 动图生成 Skill
│   ├── grid-sticker-generator/ # [NEW] 通用网格表情生成 Skill
│   ├── sticker-factory/      # [NEW] 表情包自动化工厂 Skill
│   ├── toutiao-publisher/    # 头条号发布 Skill
│   ├── video-tutorial-maker/ # 教程视频生成 Skill
│   ├── wechat-post-publisher/# [NEW] 微信公众号全自动发布图文 Skill
│   ├── wechat-red-packet-designer/ # 微信静态红包封面设计与导出 Skill
│   ├── wechat-sticker-assets-designer/ # [NEW] 微信表情包发布配套素材设计 Skill
│   └── wechat-sticker-maker/ # 微信表情包制作 Skill

├── spec/                # 规范文档
│   └── Specification.md # Agent Skills 规范
└── template/            # 模板文件
    └── SKILL.md         # 新 Skill 创建模板
```

## 🚀 使用指南

### 安装插件

#### 1. 快速安装 (推荐)
对于支持模块化技能（Skills）的 AI 助手（如 Claude Code 等），推荐直接使用 Vercel 的 `skills` CLI 在你的项目工作区中一键安装本仓库的技能，无需手动复制或克隆：

```bash
# 安装本仓库中所有的技能到项目中
npx skills@latest add guanyang/super-publisher

# 仅安装某个特定技能 (例如 toutiao-publisher 技能)
npx skills@latest add guanyang/super-publisher --skill toutiao-publisher
```

#### 2. Claude Code 插件市场
本插件同时遵循 Claude Plugin 规范，支持通过插件市场安装（适用于需要使用完整插件能力的场景）：

```bash
# 添加插件市场
/plugin marketplace add guanyang/super-publisher
# 从市场安装插件
/plugin install super-publisher@super-publisher
```

#### 3. 本地安装 / 其他 Agent
可以使用安装脚本，一键将 skills 软链接（symlink）到指定的 Agent 技能目录下：

```bash
# 默认软链接到 ~/.agent/skills 目录下
./scripts/install-skills.sh

# 或者软链接到自定义的工作区/路径下
./scripts/install-skills.sh /path/to/your/workspace/.agents/skills

# 如果需要卸载/删除已安装的软链接
./scripts/install-skills.sh --delete /path/to/your/workspace/.agents/skills
```

或者手动执行以下命令进行配置：
```bash
# 创建.agent目录
mkdir -p /path/to/your/workspace/.agents/skills
# 将skills目录复制到.agent/skills目录
cp -r skills/* /path/to/your/workspace/.agents/skills/
```
- 注意：请将`/path/to/your/workspace`替换为你的工作区路径。

### 使用 Skill
加载插件后，你可以直接通过自然语言与 Claude 交互使用相关能力，例如：
> "帮我把这篇文章发布到头条号"
> "检查头条号登录状态"
> "让参考图里的小熊抬手敬礼做成循环表情，先给我一张动图小样"
> "用小河狸做一张开工红包封面，先看完整构图和缩小效果"
> "把这个产品功能写成一支 16:9 教程视频，并生成旁白和字幕"
> "用 Excalidraw 画一张这个系统架构的可编辑示意图"

## 💡 最佳实践 (Best Practices)

### 1. 表情包生产一站式工作流
当需要从零创作并发布一套全新的微信表情包时，推荐直接使用 **Sticker Factory** (`skills/sticker-factory`)：
*   **一句话生产**：直接对 Agent 发送指令，例如：`"/sticker-factory 基于 [角色形象] 制作一套咸鱼摆烂的表情包并生成配套素材"`。
*   **全流程自动化**：工厂会自动调用 `grid-sticker-generator` 生成 16 宫格图片，接着通过 `wechat-sticker-maker` 智能切片与命名，最后调用 `wechat-sticker-assets-designer` 智能绘制适配该 IP 角色风格的 Banner 和赞赏图。
*   **统一交付归档**：所有最终成果（包含切片、图标、元数据 `meta.txt` / `info.txt` 描述及配套 Banner/赞赏图等）均统一保存在 `output/stickers_[theme]` 目录下，免去零散整理的烦恼。

用户只要预览时停在16宫格；确认后复用已选网格制作整包。配置和可执行入口见 [pack.json说明](skills/wechat-sticker-maker/references/pack-spec.md)：

```bash
python3 skills/wechat-sticker-maker/scripts/build_pack.py --spec pack.json --output output/pack_v1
```

所有导出按本地制作目标校验，不代表已通过微信审核；默认不操作草稿或提交审核。

### 2. 保证 IP 角色一致性
在生成配套素材（Banner、赞赏引导图、致谢图）时，为确保生成的图片与表情包原图的角色及画风一致：
*   **参考图机制**：先生成表情包主体网格图，并将该原图的路径或生成的第一个表情图片作为参考图传递给 Assets Designer。
*   **Prompt 约束**：在绘图 Prompt 中清晰描述 IP 角色的关键视觉特征（如“双丸子头搭配红色飘带”、“经典的黑色蘑菇头黑白简笔面部”等）并配合画风风格限定词（如“2D vector, flat illustration, bold outlines”），以获得高还原度的设计。

### 3. 公众号发布底稿洗练
发布图文到微信公众号时：
*   **自动处理多媒体与外链**：建议将本地 Markdown 编写好后，交由 `wechat-post-publisher` 进行处理。它会自动处理本地配图，上传至微信 CDN 素材库，并安全转换所有的外链，大大缩减了手动排版的时间。

## ⚙️ 规范参考
详细的 Agent Skills 格式规范请参考 [spec/Specification.md](spec/Specification.md)。

## 📝 许可证
本项目遵循 MIT 许可证。
