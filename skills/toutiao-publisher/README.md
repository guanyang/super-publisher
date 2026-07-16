# Toutiao Publisher Skill 架构与最佳实践指南

## 1. 架构原理 (Architecture)

Toutiao Publisher 是一个基于 **Playwright** 的自动化发布工具，旨在解决头条号及其复杂的富文本编辑器交互问题。其核心设计理念是 **"模拟真实用户行为" (User Simulation)** 而非简单的 API 调用。

### 1.1 核心组件

*   **`publisher.py` (核心执行器)**
    *   作为主入口，负责编排整个发布流程。
    *   **智能填充**：针对 ProseMirror 编辑器，采用多级降级策略（`execCommand` > `ClipboardEvent`）确保内容注入成功。
    *   **正文图片插入**：将 Markdown 正文图片先转换为占位符，再通过系统剪贴板在编辑器中逐张粘贴到原位置。
    *   **封面自动化**：实现了文件上传控件（`input[type=file]`）的精准定位与交互，支持本地图片上传。
    *   **明确运行模式**：`manual` 默认只填充草稿并停留在浏览器中，`validate` 只做输入预检，`auto` 才会点击最终发布按钮。
    *   **即时登录 (Login-on-the-fly)**：不再依赖分离的登录脚本，发布时若检测到未登录，自动暂停等待用户扫码，实现无缝衔接。

*   **`auth_manager.py` (凭证管理)**
    *   负责 Cookie 和 LocalStorage 的持久化。
    *   通过 `state.json` 实现免登录复用。
    *   登录前先探测受保护的发布页，并支持在线验证跨 Agent 共享浏览器配置中的登录态。
    *   认证状态支持 JSON 输出和稳定退出码，Agent 无需解析终端文案。

*   **`browser_utils.py` (环境工厂)**
    *   配置反爬虫策略（Anti-detection）。
    *   管理持久化浏览器上下文（Persistent Context），确保 UserDataDir 的正确复用。
    *   共享数据目录使用 owner-only 权限，防止其他系统用户读取 Cookie。

### 1.2 关键技术点

*   **混合输入模式**：对于标题使用标准 `fill`，对于正文使用 JS 注入，对于封面使用 `setInputFiles`。
*   **鲁棒性设计**：
    *   **Autosave 触发器**：注入内容后自动输入空格触发编辑器保存机制。
    *   **输入预检**：打开浏览器前检查标题、正文文件、正文图片、封面和运行模式。
    *   **成功判定**：自动发布必须检测到头条成功标志，不能仅凭按钮已点击推断成功。
*   **调试友好**：显式启用后在关键步骤截图（Debug Screenshots），便于排查问题。

---

## 2. 最佳实践 (Best Practices)

### 2.1 自动化草稿填充 (Automated Draft Filling)

最推荐的使用方式是通过命令行自动填充草稿，然后人工检查并手动发布。

```bash
# 标准草稿填充命令（推荐）
python3 scripts/run.py publisher.py \
  --mode manual \
  --title "你的标题（2-30字）" \
  --content-file "/absolute/path/to/article.md" \
  --cover "/absolute/path/to/cover.png"
```

*   **参数说明**：
    *   `--mode`: `manual` 人工审核、`auto` 自动发布、`validate` 仅做预检。
    *   `--title`: 自动填充时必填，必须为 2-30 字；不再静默截断。
    *   `--content-file`: UTF-8 Markdown 文件路径；`--content` 是它的别名。直接正文使用 `--content-text`。
    *   Markdown 支持标题、链接、有序/无序列表、引用、表格、代码、强调和本地正文图片。
    *   `--cover`: 图片绝对路径。建议 16:9 比例，PNG/JPG 格式。若正文 Markdown 已包含图片，脚本不会额外处理封面；只有正文没有图片时才上传该封面。
    *   `--headless`: 仅可与 `--mode auto` 组合；人工审核必须使用可见浏览器。
    *   `--json`: 输出 Agent 可解析的 JSON；发布流程使用 NDJSON 事件流。
    *   `--debug-screenshots`: 默认关闭。排查问题时开启，截图会保存到 `output/toutiao-publisher-debug/`，不会散落在当前目录。

若确实需要全自动发布，必须显式传入：

```bash
python3 scripts/run.py publisher.py \
  --mode auto \
  --title "你的标题（2-30字）" \
  --content-file "/absolute/path/to/article.md" \
  --cover "/absolute/path/to/cover.png"
```

### 2.2 登录与状态管理

*   **快速检查**：`status` 只读取本地可复用状态；增加 `--verify` 后会访问头条受保护页面做在线验证，并在成功时刷新 `state.json`：
    ```bash
    python3 scripts/run.py auth_manager.py status --verify
    ```
*   **首次使用**：直接运行发布命令（不带 `--headless`），或运行 `python3 scripts/run.py auth_manager.py setup`。`run.py` 会通过 `setup_environment.py` 自动准备 Skill 自带的 `.venv`，然后使用其中的 Python 执行认证脚本。
*   **跨 Agent 共享**：默认状态目录为 `~/.super-publisher/toutiao-publisher/`。Codex、Kiro、Antigravity 和直接 CLI 调用只要运行在同一系统用户下，就会复用同一份 Cookie 与 Chrome Profile。
*   **路径覆盖**：可通过 `SUPER_PUBLISHER_DATA_DIR` 指定其他共享位置。相对值统一按用户主目录解析，不依赖各 Agent 的启动目录：
    ```bash
    export SUPER_PUBLISHER_DATA_DIR="shared/super-publisher/toutiao"
    ```
*   **普通 Chrome 隔离**：日常使用的 Chrome Profile 仍与自动化 Profile 分开；首次登录请在脚本打开的窗口中完成。
*   **状态失效**：在线验证失败且自动重试无效时，使用内置命令清理并重新登录：
    ```bash
    # 该命令会清除所有本地 Agent 共用的登录态，先取得用户明确确认
    python3 scripts/run.py auth_manager.py clear --yes
    python3 scripts/run.py auth_manager.py setup
    ```

### 2.3 故障排查

1.  **正文为空？**
    *   这是 ProseMirror 编辑器的常见防御机制。最新版脚本已使用 `document.execCommand('insertHTML')` 解决此问题。请确保脚本是最新的。
2.  **保存失败警告？**
    *   通常是因为网络延迟。脚本会自动尝试输入空格来触发重试；自动发布模式若未检测到“草稿已保存”会直接失败，不会继续点击发布。
3.  **并发启动失败？**
    *   多个 Agent 同时打开同一 Chrome Profile 时，Chrome 自身可能拒绝启动。结束正在运行的发布任务后重试。

### 2.4 通过自然语言调用 (Natural Language Interaction)

作为 Agent Skill，最强大的用法是直接通过自然语言指令调用，Agent 会自动解析参数并执行脚本。

**场景一：发布本地 Markdown 文件**
> "帮我把 `docs/guide.md` 发布到头条，标题设为 'AI 开发指南'，封面用这张图 `assets/cover.png`。"

**场景二：生成并填充草稿**
> "写一篇关于 Python 并发编程的文章，重点介绍 Asyncio，写完后填到头条草稿里，标题自拟，并生成一张这风格的封面图一起上传。"

**场景三：仅发布正文（无封面）**
> "发布这篇文章：[粘贴文本内容]，标题是 '今日随笔'。"

**交互式登录**
> 当 Agent 提示需要登录时，不需要记忆复杂的命令，直接回复：
> "已经扫码登录了，继续吧。"

---

## 3. 目录结构

```
toutiao-publisher/
├── scripts/
│   ├── publisher.py            # 发布脚本
│   ├── setup_environment.py    # 环境配置
│   ├── config.py               # 配置文件
│   ├── auth_manager.py         # 认证模块
│   ├── browser_utils.py        # 浏览器配置
│   ├── cli_utils.py            # JSON 参数错误契约
│   ├── md2html.py              # Markdown 转换器
│   └── run.py                  # 运行入口
├── README.md                   # 本文档
├── requirements.txt            # 依赖包
└── SKILL.md                    # Skill 定义文件
```

默认运行时数据位于 `~/.super-publisher/toutiao-publisher/`，不再绑定某个
Agent 的插件安装或缓存目录。
