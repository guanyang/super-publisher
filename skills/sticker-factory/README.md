# Sticker Factory (表情包自动化工厂)

Sticker Factory 是一个**全流程编排 (Orchestration)** Skill。它充当“生产线经理”的角色，将**生成** (`grid-sticker-generator`) 和 **制作** (`wechat-sticker-maker`) 两个独立的 Skill 串联起来，实现从“一句话需求”到“最终上架素材包”的端到端自动化。

## 🏭 核心流程

工厂流水线包含三个自动化步骤：

1.  **🎨 智能生成 (Design Phase)**:
    *   调用 `grid-sticker-generator`。
    *   根据用户描述（如“熬夜的猫头鹰”），构建符合 4x4 网格、透明背景、无文字规范的 Prompt。
    *   调用绘图工具生成原始网格图。

2.  **✂️ 自动加工 (Processing Phase)**:
    *   监控生成结果，一旦拿到图片路径，立即触发加工程序。
    *   调用 `wechat-sticker-maker` 的脚本：
        *   **Auto Crop**: 按 4x4 布局自动切图。
        *   **Auto Resize**: 统一缩放至 240x240 (主图) 和 50x50 (图标)。
        *   **Meta Gen**: 生成详情页所需的 `info.txt` 和 `meta.txt`。

3.  **📦 最终交付 (Delivery Phase)**:
    *   向用户交付一个包含所有成品的文件夹路径，用户可直接用于微信表情开放平台上传。

## 📂 目录结构

```text
skills/sticker-factory/
├── README.md               # 本说明文档
└── SKILL.md                # 流水线编排逻辑
```

*注意：本 Skill 不包含具体代码脚本，它主要负责调度以下两个 Skill：*
*   `../grid-sticker-generator` (负责画)
*   `../wechat-sticker-maker` (负责切)

## 🗣️ 自然语言调用示例

这是最高效的使用方式，您只需关注结果：

### 场景一：标准生产（打工人主题）
> **User**: "工厂模式启动：帮我生产一套 '不想上班的树懒' 表情包。"
>
> **Factory**: (生成树懒的 16 种摸鱼姿态 -> 自动切图 -> 返回 output 文件夹)

### 场景二：自定义生产
> **User**: "/sticker-factory 角色是'赛博朋克风格的兔子'，生成一套用于聊天的通用表情。"
>
> **Factory**: (生成赛博兔子 16 宫格 -> 自动切图 -> 返回 output 文件夹)

## 💡 常见问题

*   **Q: 生成的图片有背景怎么办？**
    *   A: 工厂流程默认会调用切图工具的 `--remove-bg` 参数尝试自动去除背景。如果效果不理想，建议手动使用 PS 处理原图后，单独调用 `wechat-sticker-maker` 进行重切。
*   **Q: 想要更高清的图？**
    *   A: 您可以结合 `ai-image-upscaler` Skill，在生成原图后先将原图放大，然后再进行切图。
