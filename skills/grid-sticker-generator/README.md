# Universal Grid Sticker Generator (通用网格表情生成器)

这是一个专注于 **"生成 (Generation)"** 环节的核心 Skill。它定义了一套严格的视觉规范和 Prompt 构建框架，旨在指导 AI 绘图模型输出高质量、结构统一的 **4x4 表情包网格图**，为后续的自动化切图打下完美基础。

## 🎨 核心原理

本 Skill 的核心在于**标准化 (Standardization)**，通过强约束确保生成的图像可被机器识别和处理。

1.  **严格的视觉约束 (Visual Constraints)**:
    *   **布局**: 强制 **4x4 网格 (16-Grid)**，确保每个表情有独立的物理空间，互不粘连。
    *   **背景**: 强制 **透明背景 (Transparent Background)**，减少后续去底的难度和瑕疵。
    *   **风格**: 强制 **扁平矢量 (Flat Vector)** 和 **无描边 (No Outline)**，确保缩放不失真，边缘干净。

2.  **内容纯净 (Content Purity)**:
    *   **零文字原则**: 严禁生成汉字、英文或对话气泡。所有的情绪表达必须通过肢体语言和通用漫符（如 💢, 💦）完成。

3.  **模板化引擎 (Templating Engine)**:
    *   Skill 支持加载 `resources/` 下的主题模板。
    *   **默认行为**: 调用内置的 `office_worker_template.md`（打工人模板），自动填充“摸鱼”、“加班”等职场梗。
    *   **通用行为**: 也支持用户自定义主题（如“快乐小狗”），Skill 会根据通用 4x4 规范生成多样化的动作。

## 📂 目录结构

```text
skills/grid-sticker-generator/
├── README.md               # 本说明文档
├── SKILL.md                # 核心 Prompts 构建逻辑
└── resources/              # 提示词模板库
    └── office_worker_template.md  # [内置] 打工人主题模板
```

## 🗣️ 自然语言调用示例

在 Agent 交互中，你可以通过描述**角色**和**主题**来触发此 Skill：

### 场景一：使用内置“打工人”模板
> **User**: "生成一个 '秃顶的猫咪程序员' 表情包。"
>
> **Agent**: (自动加载 Office Worker 模板，将猫咪形象代入“代码报错”、“背锅”等 16 个经典场景生成网格图)

### 场景二：自定义主题
> **User**: "生成一套 'Q版哥斯拉' 表情包，要包含喷火、拆楼、睡觉等动作。"
>
> **Agent**: (使用通用 4x4 规范，生成哥斯拉的 16 个自定义动作网格图)

## 💡 最佳实践

*   **角色描述越具体越好**: 比如 "A cute panda wearing glasses and a blue hoodie" 比单纯 "A panda" 效果更好。
*   **强调无字**: 虽然 Skill 已经加了负面提示词，但在复杂 prompt 中，模型偶尔会“幻视”。如果生成了文字，可以重试并强调 "NO TEXT"。
