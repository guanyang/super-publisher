# 更新日志

本项目的所有重要更改都将记录在此文件中。

## [1.4.2] - 2026-06-22
### 🚀 新增功能
- **Excalidraw Visual Designer** (`skills/excalidraw-visual-designer`):
  - **可编辑视觉设计**: 支持通过 Excalidraw 创建和修改图表、流程图、架构草图、信息图、教学视觉和宣传版式。
  - **Clipboard JSON 导入**: 新增 `scripts/make_excalidraw_clipboard.py`，可将任务级场景规格转换为 Excalidraw clipboard JSON。
  - **连线质量规则**: 内置箭头绕行、标签避让、截图复查和版面层级检查流程，降低复杂图形中的遮挡与交叉问题。

## [1.4.1] - 2026-06-16
### 🚀 新增功能
- **Video Tutorial Maker** (`skills/video-tutorial-maker`):
  - **教程视频包生成**: 支持将主题、提纲、脚本或既有视频转成带旁白、字幕和场景规划的教程视频制作流程。
  - **音画字幕同步规范**: 明确按场景生成 TTS、字幕时间线和补齐后的音频，降低多片段拼接时的漂移风险。
  - **平台变体输出**: 默认指导生成 1920x1080 横屏 MP4，并提供 9:16 无裁切转换模式。

### 🛠 改进与修复
- **Toutiao Publisher** (`skills/toutiao-publisher`):
  - **默认人工发布确认**: 自动填充文章后默认停在头条编辑器，不再自动点击最终发布按钮；仅在显式传入 `--auto-publish` 时执行发布。
  - **正文图片上传**: 支持将 Markdown 正文图片转换为占位符，并在编辑器内按原位置逐张粘贴上传。
  - **封面处理策略优化**: 当正文已包含图片时跳过显式封面上传，避免触发头条封面选择弹框；仅在正文无图片且提供 `--cover` 时上传封面。
  - **调试截图默认关闭**: 默认不再在当前目录生成 `debug_*.png`，仅在传入 `--debug-screenshots` 时保存到 `output/toutiao-publisher-debug/`。

## [1.4.0] - 2026-06-09
### 🚀 新增功能
- **WeChat Sticker Assets Designer** (`skills/wechat-sticker-assets-designer`):
  - **配套宣传素材设计师**: 根据表情包 IP 形象特征，自动生成符合官方规格的微信横幅 (Banner)、赞赏引导图和赞赏致谢图。
  - **中文字体文案整合**: 支持在引导图与致谢图中优雅融合官方指定文案。
  - **自动尺寸校准**: 内置 Pillow 条件裁剪与缩放脚本 `crop_and_resize.py`，并提供 `run.sh` 自动环境管理包装，实现官方比例精准切图。

### 🛠 改进与重构
- **WeChat Sticker Maker**:
  - **环境极致轻量化**: 彻底移除了效果欠佳的重型 `--remove-bg` 背景消除功能以及对应的 `rembg`、`onnxruntime` 库依赖，大幅提升 Skill 初始化及装载速度。
  - **输出目录自定义**: 支持并指引 Agent 传入自定义目标文件夹（默认为 `output/stickers_[theme]` 格式），更贴合实际工程目录规范。
- **Sticker Factory**:
  - **全流程并轨生产**: 将配套宣传素材设计技能（`wechat-sticker-assets-designer`）整合到表情包自动生产流水线中。
  - **输出目录统一化**: 实现将生成的表情包主体包和配套宣传素材合并输出到同一个总目录下，素材文件整理于 `assets/` 子目录，消除零散输出。

## [1.3.0] - 2026-04-10
### 🚀 新增功能
- **WeChat Post Publisher** (`skills/wechat-post-publisher`):
  - **自动化极客大模型发文引擎**: 支持把本地 Markdown 无损跨端转译兼容微信后台，并实现图片素材并轨全自动上传。
  - **智能化原生兼容**: 深度适配 Agent / LLM 系统指令态对话操控模式（Slash Command 闭环直取）。
  - **多租户高级微沙箱隔离**: 原生实现 `EXTEND.md` 结合 `Alias 别名` 映射逻辑，在一套仓库下轻松维护千万个隔离环境配置的账号矩阵。

## [1.2.0] - 2026-02-02
### 🚀 新增功能
- **GIF Maker** (`skills/gif-maker`):
  - **序列帧转 GIF**: 支持将图片序列合并为高质量 GIF。
  - **精灵表转 GIF**: 支持直接读取网格拼图（如 4x4）切分并生成动画。
  - **智能压缩**: 集成 `gifsicle`，支持通过 `--max-size` 参数自动压制文件体积，确保符合微信表情包规范（<1MB）。

### 🛠 改进
- **WeChat Sticker Maker**:
  - 更新文档，增加详细的使用指南和原理说明。
  - 增强脚本健壮性。

## [1.1.0] - 2026-01-28
### 🚀 新增功能
- **表情包自动化流水线**:
  - **Sticker Factory** (`skills/sticker-factory`): 全流程编排 Skill，实现从 prompt 到微信素材包的一键生产。
  - **Grid Sticker Generator** (`skills/grid-sticker-generator`): 通用 4x4 网格表情生成器，支持“无字/透底”视觉规范及模板加载。
  
### 🛠 改进
- **WeChat Sticker Maker**:
  - 增加 `run.sh` 启动脚本，支持**全自动环境管理**（自动创建 venv、安装依赖）。
  - 优化去底逻辑，增加对复杂背景的处理提示。
  - 重构脚本位置，统一归档至 `scripts/` 目录。
## [1.0.0] - 2026-01-16

### 🎉 初始发布
- 发布 **Super Publisher** 插件，专为 Agentic 工作流自动化设计。

### 🚀 新增功能
- **Toutiao Publisher Skill** (`skills/toutiao-publisher`):
  - 实现发布文章到头条号（今日头条）的自动化。
  - **持久化认证**：采用持久化浏览器上下文，实现“一次扫码，长期有效”的免登录机制。
  - **智能编辑器交互**：针对 ProseMirror 编辑器，采用混合输入策略（execCommand + ClipboardEvents）确保内容稳定注入。
  - **自动优化**：支持标题自动截断（2-30字符）及 Markdown 转 HTML。
  - **无头模式**：支持后台静默运行，无需干扰前台操作。

- **插件架构**:
  - 完整支持 **Claude Plugin** 规范 (`.claude-plugin/plugin.json`)。
  - 集成 **Antigravity IDE** 支持，实现 Skill 的无缝发现与调用。

### 📚 文档
- 新增详尽的 `README.md`，包含 Claude Code 和 Antigravity 的安装指南。
- 新增 Toutiao Publisher 的 **架构原理与最佳实践指南**。
- 新增标准 `template/SKILL.md` 用于扩展新能力。

### 🛠 改进
- 优化 `publisher.py`，增加了自动保存检测和多步发布确认机制。
- 增加了对文件上传和遮罩层处理的严格类型检查。
