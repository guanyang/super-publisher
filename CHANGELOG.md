# 更新日志

本项目的所有重要更改都将记录在此文件中。
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
