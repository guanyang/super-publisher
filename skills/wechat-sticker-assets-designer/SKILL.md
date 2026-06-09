---
name: wechat-sticker-assets-designer
description: "微信表情包发布配套素材（横幅 Banner、赞赏引导图、致谢图）设计与生成工具。能够精准分析 IP 角色风格并按照官方规格及文案规范生成高清宣传素材。"
compatibility: Requires AI image generation tools (such as generate_image or equivalent drawing tools).
---

# WeChat Sticker Assets Designer (微信表情包配套素材设计师)

本 Skill 旨在协助 Agent 扮演专业的设计师角色，分析用户已有的表情包 IP 形象，并严格按照微信表情开放平台的规格标准，依次生成**横幅 (Banner)**、**赞赏引导图**和**赞赏致谢图**。

---

## 🎨 核心约束 (Global Constraints)

1.  **IP 角色一致性 (Character Consistency)**：
    *   在生成所有 3 张图片时，必须严格保留并继承用户参考图中的 IP 核心特征（例如：发型、配饰、五官比例、经典色调等）。必须确保是同一个角色在不同场景下的演绎。
2.  **严禁包含 Emoji 表情**：
    *   所有生成的图像画面中，**绝对不能**出现任何 Emoji 符号（如 😂, ❤️, 👍 等）。
3.  **图画格式规范**：
    *   在构建绘图 Prompt 时，明确描述干净、扁平、矢量插画等有利于呈现 PNG 质感的风格词，确保边缘整洁。
4.  **单步依次输出 (Sequential Output)**：
    *   必须按照工作流，一张接一张独立调用工具生成并展示，**严禁**将多张图合并拼接成一张长图。

---

## 📏 图像生成规格 (Detailed Specs)

### 第一张：微信横幅 (Banner)
*   **尺寸比例**：`750x400` 像素 (宽长比约 1.875:1，Prompt 中设置比例，如 `--ar 15:8` 或 `1.875:1 aspect ratio`)。
*   **画面内容**：
    *   设计一个以该 IP 角色为核心、具有**故事性**和**丰富细节**的完整场景（如：角色在太空探险、在森林露营或在桌前创作等）。
    *   色调活泼明朗。
    *   **背景约束 (极重要)**：背景**严禁使用白色**，也**严禁使用透明背景**，必须有饱满的带色彩背景，以在微信浅色界面中形成清晰的视觉边界。
*   **文字约束**：**画面中严禁出现任何文字或乱码**。

### 第二张：赞赏引导图 (Solicitation Image)
*   **尺寸比例**：`750x560` 像素 (宽长比约 1.34:1，Prompt 中设置比例，如 `--ar 4:3` 或 `1.34:1 aspect ratio`)。
*   **画面内容**：
    *   角色需要展现出“期待支持”、“可爱卖萌”或“双手捧碗/求打赏”的神态与动作，增强赞赏吸引力。
    *   **背景约束**：**严禁使用白色或接近白色的浅色背景与边缘**。背景必须为实色且深于微信页面底色。
*   **文案要求**：
    *   **必须在画面合适位置完美融合中文文字**：“您的赞赏是我们最大的动力！”。
    *   文字的字体、颜色和风格需与整体画面插画风格保持高度一致。

### 第三张：赞赏致谢图 (Acknowledgment Image)
*   **尺寸比例**：`750x750` 像素 (1:1 正方形比例，Prompt 中设置比例 `--ar 1:1`)。
*   **画面内容**：
    *   角色展现出“极其感激”、“庆祝”、“撒花欢呼”或“双手比心致谢”的开心状态。
    *   画面色彩丰富饱满，营造出喜庆、欢快的互动氛围，激发分享欲。
    *   **背景约束**：**严禁使用白色或接近白色的浅色背景与边缘**。
*   **文案要求**：
    *   **必须在画面合适位置完美融合中文文字**：“感谢您的慷慨赞赏！”。
    *   文字的排版和设计需与画面插画风格保持和谐。

---

## 🛠️ 使用指南 (Usage Guide)

### 1. 快速开始 (Quick Start)

无需手动安装依赖，直接运行脚本即可。工具会自动创建虚拟环境 (`.venv`) 并安装所需依赖。

```bash
# 横幅 Banner (目标 750x400，采用居中 center 裁剪)
./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_BANNER" --width 750 --height 400 --anchor center

# 赞赏引导图 (目标 750x560，采用靠上 top 裁剪以防切掉顶部文字)
./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_SOLICITATION" --width 750 --height 560 --anchor top

# 赞赏致谢图 (目标 750x750，采用居中 center 缩放)
./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_ACKNOWLEDGMENT" --width 750 --height 750 --anchor center
```

### 2. (可选) 手动安装

如果您希望手动管理环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r skills/wechat-sticker-assets-designer/requirements.txt
python3 skills/wechat-sticker-assets-designer/scripts/crop_and_resize.py ...
```

---

## 🛠️ 执行工作流 (Execution Workflow)

Agent 激活本技能后，需严格按以下四个步骤执行：

1.  **第一步：分析 IP 角色风格**。
    *   阅读并分析用户提供的【表情示例图】或角色描述，提取并总结出角色的线条笔触、色彩搭配及标志性特征（如“双丸子头、红飘带的哪吒角色”）。
2.  **第二步：生成横幅 (Banner)**。
    *   构建绘图 Prompt 描述符合 Banner 规格的丰富故事场景，调用 `generate_image` 生成。
    *   检查生成的图片：确保**无任何文字**且**无白色/透明背景**。
3.  **第三步：生成赞赏引导图**。
    *   构建 Prompt 描述角色期待卖萌的姿态，并加入包含文案“您的赞赏是我们最大的动力！”的排版指示，调用 `generate_image` 生成。
    *   检查背景是否非白。
4.  **第四步：生成赞赏致谢图**。
    *   构建 Prompt 描述角色狂欢致谢、比心的开心姿态，并加入包含文案“感谢您的慷慨赞赏！”的排版指示，调用 `generate_image` 生成。
5.  **第五步：输出结果核对与裁剪 (CRITICAL CHECK & CROP)**。
    *   **重要说明 (脚本条件化裁剪)**：由于绘图工具可能默认输出 1:1 图片，Agent **必须**在生成完成后使用本技能内置的裁剪脚本来执行条件化尺寸核准（只有在尺寸不符时才会真正执行裁剪和缩放）：
        *   运行脚本命令样例（推荐使用 `run.sh` 脚本）：
            ```bash
            # 横幅 Banner (目标 750x400，采用居中 center 裁剪)
            ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_BANNER" --width 750 --height 400 --anchor center
            
            # 赞赏引导图 (目标 750x560，采用靠上 top 裁剪以防切掉顶部文字)
            ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_SOLICITATION" --width 750 --height 560 --anchor top
            
            # 赞赏致谢图 (目标 750x750，采用居中 center 缩放)
            ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_ACKNOWLEDGMENT" --width 750 --height 750 --anchor center
            ```
    *   在交付前，Agent **必须显式确认三张素材的最终像素尺寸已完全符合要求**。
    *   **强约束**：如果因为任何绘图工具故障导致任何一张图缺失，**必须立即重新调用生图工具补全生成**，绝不能只交付部分素材。
    *   最终将这 3 张独立图片复制/保存到用户指定的输出目录下（如果未指定，默认创建 `output/sticker_assets_[theme]` 目录），并向用户呈报绝对路径、画幅规格与预览。
