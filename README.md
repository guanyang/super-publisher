# Super Publisher

Super Publisher 是一个专为 Agent 设计的插件，旨在实现自动化的多平台内容发布。目前核心集成了头条号（Toutiao）的自动化发布能力，后续会集成更多平台。

## 🌟 核心功能

### Toutiao Publisher (`skills/toutiao-publisher`)
> 架构原理及最佳实践请参考[skills/toutiao-publisher](skills/toutiao-publisher/README.md)。
- **持久化登录**：一次扫码，长期有效，自动管理 Session。
- **自动化发布**：通过命令行或自然语言指令自动发布文章。
- **智能适配**：自动优化标题长度，支持 Markdown 转 HTML。
- **无头模式**：支持后台静默运行。

## 📂 项目结构

```
.
├── .claude-plugin/      # Claude 插件配置文件
│   ├── plugin.json      # 插件清单文件
│   └── marketplace.json # 市场发布配置
├── skills/              # Agent Skills 目录
│   └── toutiao-publisher/ # 头条号发布 Skill
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

#### 2. Antigravity
执行以下命令配置skills目录下的能力：
```bash
# 创建.agent目录
mkdir -p /path/to/your/workspace/.agent/skills
# 将skills目录复制到.agent/skills目录
cp -r skills/* /path/to/your/workspace/.agent/skills/
```
- 注意：请将`/path/to/your/workspace`替换为你的工作区路径。

### 使用 Skill
加载插件后，你可以直接通过自然语言与 Claude 交互使用相关能力，例如：
> "帮我把这篇文章发布到头条号"
> "检查头条号登录状态"

## 🛠 开发指南

### 创建新 Skill
1. 复制 `template/SKILL.md` 到 `skills/<new-skill-name>/SKILL.md`。
2. 按照 `spec/Specification.md` 中的规范完善 Skill 定义。
3. 在 `skills/<new-skill-name>/` 目录下实现具体的脚本和逻辑。

### 规范参考
详细的 Agent Skills 格式规范请参考 [spec/Specification.md](spec/Specification.md)。

## 📝 许可证
本项目遵循 MIT 许可证。