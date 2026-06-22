# Super Publisher

Super Publisher 是一个专为 Agent 设计的插件，旨在实现自动化的多平台内容发布。

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

### WeChat Sticker Maker (`skills/wechat-sticker-maker`)
> 详细文档请参考 [skills/wechat-sticker-maker/README.md](skills/wechat-sticker-maker/README.md)。
- **智能切分**：自动识别或指定网格布局（九宫格、十六宫格等），精准切分拼图。
- **规范适配**：自动生成符合微信规范的 240x240 主图和 50x50 聊天页图标。
- **元数据生成**：自动生成含义词配置表 (`meta.txt`) 和专辑信息模板 (`info.txt`)，加速提交流程。

### WeChat Sticker Assets Designer (`skills/wechat-sticker-assets-designer`)
> 详细文档请参考 [skills/wechat-sticker-assets-designer/README.md](skills/wechat-sticker-assets-designer/README.md)。
- **规范化生成**：根据用户提供的表情包 IP 形象，一键生成符合微信表情官方规范的横幅 (Banner, 750x400)、赞赏引导图 (750x560) 和赞赏致谢图 (750x750)。
- **条件化裁剪**：内置 Pillow 条件裁剪与缩放脚本，确保导出的图稿像素和构图精准无误。
- **文案深度整合**：支持自动排版和在引导图及致谢图中完美融入指定官方中文字体文案。

### Grid Sticker Generator (`skills/grid-sticker-generator`)
> 详细文档请参考 [skills/grid-sticker-generator/README.md](skills/grid-sticker-generator/README.md)。
- **通用生成**：基于标准化的 4x4 网格视觉规范，生成无字、透底、矢量风格的网格图。
- **模板支持**：内置“打工人”模板，支持加载不同主题的梗库和动作列表。

### Sticker Factory (`skills/sticker-factory`)
> 详细文档请参考 [skills/sticker-factory/README.md](skills/sticker-factory/README.md)。
- **全流程编排**：作为“工厂经理”，串联网格生成器、表情包切片制作器及配套宣传素材设计器。
- **一键整合交付**：从自然语言需求（如 "生成一套快乐小狗表情包"）直接产出包含表情包切片、图标、元数据以及裁剪好的配套 Banner 与赞赏致谢图的一体化输出目录。

### GIF Maker (`skills/gif-maker`)
> 详细文档请参考 [skills/gif-maker/README.md](skills/gif-maker/README.md)。
- **动图生成**：支持从序列帧或网格图（Sprite Sheet）生成 GIF 动画。
- **智能压缩**：专为表情包设计，支持 `--max-size` 参数，自动将 GIF 压制在微信限制（1MB/500KB）以内。
- **参数灵活**：支持自定义 FPS、布局切分及循环模式。

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
│   ├── excalidraw-visual-designer/ # Excalidraw 可编辑视觉设计 Skill
│   ├── gif-maker/            # [NEW] GIF 动图生成 Skill
│   ├── grid-sticker-generator/ # [NEW] 通用网格表情生成 Skill
│   ├── sticker-factory/      # [NEW] 表情包自动化工厂 Skill
│   ├── toutiao-publisher/    # 头条号发布 Skill
│   ├── video-tutorial-maker/ # 教程视频生成 Skill
│   ├── wechat-post-publisher/# [NEW] 微信公众号全自动发布图文 Skill
│   ├── wechat-sticker-assets-designer/ # [NEW] 微信表情包发布配套素材设计 Skill
│   └── wechat-sticker-maker/ # 微信表情包制作 Skill

├── spec/                # 规范文档
│   └── Specification.md # Agent Skills 规范
└── template/            # 模板文件
    └── SKILL.md         # 新 Skill 创建模板
```

## 🚀 使用指南

### 安装插件

本插件遵循 Claude Plugin 规范，支持多种 Agent 环境加载。

#### 1. Claude Code
在启动 Claude Code 之后，执行以下命令加载插件：

```bash
# 添加插件市场
/plugin marketplace add guanyang/super-publisher
# 从市场安装插件
/plugin install super-publisher@super-publisher
```

#### 2. 本地安装 / 其他 Agent
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
> "把这个产品功能写成一支 16:9 教程视频，并生成旁白和字幕"
> "用 Excalidraw 画一张这个系统架构的可编辑示意图"

## 💡 最佳实践 (Best Practices)

### 1. 表情包生产一站式工作流
当需要从零创作并发布一套全新的微信表情包时，推荐直接使用 **Sticker Factory** (`skills/sticker-factory`)：
*   **一句话生产**：直接对 Agent 发送指令，例如：`"/sticker-factory 基于 [角色形象] 制作一套咸鱼摆烂的表情包并生成配套素材"`。
*   **全流程自动化**：工厂会自动调用 `grid-sticker-generator` 生成 16 宫格图片，接着通过 `wechat-sticker-maker` 智能切片与命名，最后调用 `wechat-sticker-assets-designer` 智能绘制适配该 IP 角色风格的 Banner 和赞赏图。
*   **统一交付归档**：所有最终成果（包含切片、图标、元数据 `meta.txt` / `info.txt` 描述及配套 Banner/赞赏图等）均统一保存在 `output/stickers_[theme]` 目录下，免去零散整理的烦恼。

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
