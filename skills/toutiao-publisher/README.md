# Toutiao Publisher Skill 架构与最佳实践指南

## 1. 架构原理 (Architecture)

Toutiao Publisher 是一个基于 **Playwright** 的自动化发布工具，旨在解决头条号及其复杂的富文本编辑器交互问题。其核心设计理念是 **"模拟真实用户行为" (User Simulation)** 而非简单的 API 调用。

### 1.1 核心组件

*   **`publisher.py` (核心执行器)**
    *   作为主入口，负责编排整个发布流程。
    *   **智能填充**：针对 ProseMirror 编辑器，采用多级降级策略（`execCommand` > `ClipboardEvent`）确保内容注入成功。
    *   **正文图片插入**：将 Markdown 正文图片先转换为占位符，再通过系统剪贴板在编辑器中逐张粘贴到原位置。
    *   **封面自动化**：实现了文件上传控件（`input[type=file]`）的精准定位与交互，支持本地图片上传。
    *   **人工发布确认**：默认只填充草稿并停留在浏览器中，最终发布由用户检查后手动点击；只有显式传入 `--auto-publish` 才会点击发布按钮。
    *   **即时登录 (Login-on-the-fly)**：不再依赖分离的登录脚本，发布时若检测到未登录，自动暂停等待用户扫码，实现无缝衔接。

*   **`auth_manager.py` (凭证管理)**
    *   负责 Cookie 和 LocalStorage 的持久化。
    *   通过 `state.json` 实现免登录复用。
    *   包含自动检测 Cookie 有效性的逻辑。

*   **`browser_utils.py` (环境工厂)**
    *   配置反爬虫策略（Anti-detection）。
    *   管理持久化浏览器上下文（Persistent Context），确保 UserDataDir 的正确复用。

### 1.2 关键技术点

*   **混合输入模式**：对于标题使用标准 `fill`，对于正文使用 JS 注入，对于封面使用 `setInputFiles`。
*   **鲁棒性设计**：
    *   **Autosave 触发器**：注入内容后自动输入空格触发编辑器保存机制。
    *   **动态等待**：从不使用固定 `sleep`，而是基于 `wait_for_selector` 和状态轮询。
*   **调试友好**：关键步骤自动截图（Debug Screenshots），便于排查无头模式下的问题。

---

## 2. 最佳实践 (Best Practices)

### 2.1 自动化草稿填充 (Automated Draft Filling)

最推荐的使用方式是通过命令行自动填充草稿，然后人工检查并手动发布。

```bash
# 标准草稿填充命令（推荐）
python scripts/run.py publisher.py \
  --title "你的标题（2-30字）" \
  --content "/absolute/path/to/article.md" \
  --cover "/absolute/path/to/cover.png"
```

*   **参数说明**：
    *   `--title`: 必填。脚本会自动截断超长标题。
    *   `--content`: 支持 Markdown 文件路径或直接文本串。自动转换为 HTML。Markdown 正文图片会按原位置插入，推荐使用本地图片路径。
    *   `--cover`: 图片绝对路径。建议 16:9 比例，PNG/JPG 格式。若正文 Markdown 已包含图片，脚本不会额外处理封面；只有正文没有图片时才上传该封面。
    *   `--auto-publish`: 显式启用最终发布按钮点击。默认不传，保留人工检查。
    *   `--headless`: 加上此参数可在后台运行（需确保已登录）。人工发布检查需要可见浏览器，因此默认流程不建议加。
    *   `--debug-screenshots`: 默认关闭。排查问题时开启，截图会保存到 `output/toutiao-publisher-debug/`，不会散落在当前目录。

若确实需要全自动发布，必须显式传入：

```bash
python scripts/run.py publisher.py \
  --title "你的标题（2-30字）" \
  --content "/absolute/path/to/article.md" \
  --cover "/absolute/path/to/cover.png" \
  --auto-publish
```

### 2.2 登录与状态管理

*   **首次使用**：直接运行发布命令（不带 `--headless`）。脚本会自动弹出浏览器，请扫码登录。登录后脚本会自动保存状态。
*   **状态失效**：如果遇到 `No valid authentication` 且自动重试无效，可手动清理状态：
    ```bash
    rm -rf data/browser_state
    ```
    然后重新运行发布命令。

### 2.3 故障排查

1.  **正文为空？**
    *   这是 ProseMirror 编辑器的常见防御机制。最新版脚本已使用 `document.execCommand('insertHTML')` 解决此问题。请确保脚本是最新的。
2.  **保存失败警告？**
    *   通常是因为网络延迟。脚本会自动尝试输入空格来触发重试。只要最终能点击“发布”，通常说明保存已成功。
3.  **进程锁定 (TargetClosedError)？**
    *   这是因为上一次运行异常退出，导致 Chrome 锁定了 `UserDataDir`。
    *   **解决**：运行 `pkill -f "Chrome"` 或重启终端。

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
│   ├── md2html.py              # Markdown 转换器
│   └── run.py                  # 运行入口
├── data/                       # 数据目录，运行时存本地
│   └── browser_state/          # 存储 Cookie 和 Profile（自动生成）
├── README.md                   # 本文档
├── requirements.txt            # 依赖包
└── SKILL.md                    # Skill 定义文件
```
