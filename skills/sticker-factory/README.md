# Sticker Factory (表情包自动化工厂)

Sticker Factory 是一个**全流程编排 (Orchestration)** Skill。它充当“生产线经理”的角色，将**生成** (`grid-sticker-generator`) 和 **制作** (`wechat-sticker-maker`) 两个独立的 Skill 串联起来，实现从“一句话需求”到“最终上架素材包”的端到端自动化。

## 🏭 核心流程

工厂流水线包含四个自动化步骤：

1.  **🎨 智能生成 (Design Phase)**:
    *   调用 `grid-sticker-generator`。
    *   根据用户描述（如“熬夜的猫头鹰”），构建符合 4x4 网格、透明背景、无文字规范的 Prompt。
    *   调用绘图工具生成原始网格图。

2.  **✂️ 自动加工 (Processing Phase)**:
    *   监控生成结果，一旦拿到图片路径，立即触发加工程序。
    *   调用 `wechat-sticker-maker` 的脚本：
        *   **Auto Crop**: 按 4x4 布局自动切图。
        *   **Auto Resize**: 统一缩放至 240x240 (主图) 和 50x50 (图标)。
        *   **Meta Gen**: 自动修改填充详情页所需的 `info.txt` 和 `meta.txt`。

3.  **🖼️ 配套设计 (Assets Phase)**:
    *   调用 `wechat-sticker-assets-designer` 技能。
    *   分析已生成的 IP 角色视觉特征，分别生成横幅 (Banner, 750x400)、赞赏引导图 (750x560, 融合指定文案)、赞赏致谢图 (750x750, 融合指定文案)。
    *   自动运行 `run.sh` 脚本执行条件化裁剪，得到精确官方尺寸的成品。

4.  **📦 最终交付 (Delivery Phase)**:
    *   向用户交付整合后的表情包输出目录的绝对路径（配套素材包含在内部的 `assets/` 子目录中），并呈报图片预览。

## 📂 目录结构

```text
skills/sticker-factory/
├── README.md               # 本说明文档
└── SKILL.md                # 流水线编排逻辑
```

*注意：本 Skill 不包含具体代码脚本，它主要负责调度以下三个 Skill：*
*   `../grid-sticker-generator` (负责画)
*   `../wechat-sticker-maker` (负责切)
*   `../wechat-sticker-assets-designer` (负责画微信配套 Banner、赞赏图及裁剪)

## 🗣️ 自然语言调用示例

这是最高效的使用方式，您只需关注结果：

### 场景一：标准生产（打工人主题 + 配套素材）
> **User**: "工厂模式启动：帮我生产一套 '不想上班的树懒' 表情包。"
>
> **Factory**: (生成树懒的 16 种摸鱼姿态 -> 自动切图 -> 自动生成配套横幅与赞赏图并裁剪到 `assets/` 子目录 -> 返回整合后的输出目录)

### 场景二：自定义生产
> **User**: "/sticker-factory 角色是'赛博朋克风格的兔子'，生成一套用于聊天的通用表情及相关发布素材。"
>
> **Factory**: (生成赛博兔子 16 宫格 -> 自动切图 -> 自动生成配套横幅与赞赏图并裁剪到 `assets/` 子目录 -> 返回整合后的输出目录)

## 💡 常见问题

*   **Q: 想要更高清的图？**
    *   A: 您可以结合 `ai-image-upscaler` Skill，在生成原图后先将原图放大，然后再进行切图与后续处理。
