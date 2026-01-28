# Super Publisher

Super Publisher 是一个专为 Agent 设计的插件，旨在实现自动化的多平台内容发布。

## 🌟 核心功能

### Toutiao Publisher (`skills/toutiao-publisher`)
> 架构原理及最佳实践请参考[skills/toutiao-publisher](skills/toutiao-publisher/README.md)。
- **持久化登录**：一次扫码，长期有效，自动管理 Session。
- **自动化发布**：通过命令行或自然语言指令自动发布文章。
- **智能适配**：自动优化标题长度，支持 Markdown 转 HTML。
- **无头模式**：支持后台静默运行。

### WeChat Sticker Maker (`skills/wechat-sticker-maker`)
> 详细文档请参考 [skills/wechat-sticker-maker/README.md](skills/wechat-sticker-maker/README.md)。
- **智能切分**：自动识别或指定网格布局（九宫格、十六宫格等），精准切分拼图。
- **规范适配**：自动生成符合微信规范的 240x240 主图和 50x50 聊天页图标。
- **AI 去底**：内置 `rembg` 智能去背功能，支持一键移除复杂背景（可选）。
- **元数据生成**：自动生成含义词配置表 (`meta.txt`) 和专辑信息模板 (`info.txt`)，加速提交流程。

### Grid Sticker Generator (`skills/grid-sticker-generator`)
> 详细文档请参考 [skills/grid-sticker-generator/README.md](skills/grid-sticker-generator/README.md)。
- **通用生成**：基于标准化的 4x4 网格视觉规范，生成无字、透底、矢量风格的网格图。
- **模板支持**：内置“打工人”模板，支持加载不同主题的梗库和动作列表。

### Sticker Factory (`skills/sticker-factory`)
> 详细文档请参考 [skills/sticker-factory/README.md](skills/sticker-factory/README.md)。
- **全流程编排**：作为“工厂经理”，串联生成器和制作器。
- **一键交付**：从自然语言需求（"生成一套快乐小狗表情包"）直接产出可提交的素材包。

## 📂 项目结构

```
.
├── .claude-plugin/      # Claude 插件配置文件
├── skills/              # Agent Skills 目录
│   ├── grid-sticker-generator/ # [NEW] 通用网格表情生成 Skill
│   ├── sticker-factory/      # [NEW] 表情包自动化工厂 Skill
│   ├── toutiao-publisher/    # 头条号发布 Skill
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