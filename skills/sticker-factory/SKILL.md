---
name: sticker-factory
description: "Automated factory workflow: Generates grid-based sticker sheets and auto-packages them for WeChat using wechat-sticker-maker. Use when the user wants to create a complete custom sticker pack from scratch (e.g., '帮我做一套表情包', '批量生产表情')."
compatibility: Requires AI image generation tools (such as generate_image) and local execution environment for WeChat sticker maker scripts.
---

# Sticker Factory (Auto-Generator & Packer)

This skill serves as an **Automated Production Line** that orchestrates the entire lifecycle of sticker creation: from AI generation to WeChat-compliant asset packaging.

## Execution Workflow

### Step 1: Generate Sticker Grid
Adhere to the **Universal Grid Logic** defined in `skills/grid-sticker-generator/SKILL.md`.

*   **Prompt Construction**:
    *   **Core**: User's described character/theme.
    *   **Format Constraints (CRITICAL)**: Inherit all **Visual Design Standards** from `grid-sticker-generator` (4x4 Grid, No Text, Flat Vector).
    *   **Content Logic**:
        *   **Default**: Load the **Office Worker Template** (`references/office_worker_template.md`) from the generator skill to fill slots with office memes.
        *   **Custom**: If user specifies a different theme, generate 16 varied actions relevant to that theme satisfying the grid constraints.

*   **Action**:
    *   Call `generate_image` with the constructed prompt.

### Step 2: Auto-Process with Sticker Maker
Once the image is successfully generated, **immediately** trigger the packaging robot.

*   **Command**:
    ```bash
    ./skills/wechat-sticker-maker/scripts/run.sh "PATH_TO_GENERATED_IMAGE" --output "OUTPUT_DIR" --layout 4x4
    ```
    *   *PATH_TO_GENERATED_IMAGE*: The absolute path returned by the `generate_image` tool.
    *   *OUTPUT_DIR*: If user specified a custom path, use it. Otherwise, default to `output/stickers_[theme]`.

*   **Metadata Auto-Population (CRITICAL)**:
    Before moving to the next step, the Agent **must**:
    *   Automatically edit and fill in `info.txt` and `meta.txt` with actual names, descriptions, and sticker meaning words, replacing the template placeholders, based on the theme generated.
    *   Copy the original generated grid image into the output folder (e.g. as `source.png` or `grid_image.png`).

### Step 3: Generate Matching WeChat Sticker Assets
Orchestrate the design of matching promotional materials based on the generated IP character using `skills/wechat-sticker-assets-designer/SKILL.md`.

*   **Action**:
    1.  **Analyze IP**: Extract visual features (hair, colors, outfit) from the generated grid image.
    2.  **Generate Assets**:
        *   **Banner**: Aspect ratio 15:8 (`750x400` target). Rich story-rich scene, no text, no white/transparent background.
        *   **Solicitation Image**: Aspect ratio 4:3 (`750x560` target). Begging pose, including text "您的赞赏是我们最大的动力！", non-white background.
        *   **Acknowledgment Image**: Aspect ratio 1:1 (`750x750` target). Celebratory pose, including text "感谢您的慷慨赞赏！", non-white background.
    3.  **Crop & Resize**:
        Run the conditional crop and resize wrapper script on each generated asset to achieve the exact WeChat specification sizes:
        ```bash
        ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_BANNER" --width 750 --height 400 --anchor center
        ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_SOLICITATION" --width 750 --height 560 --anchor top
        ./skills/wechat-sticker-assets-designer/scripts/run.sh "PATH_TO_ACKNOWLEDGMENT" --width 750 --height 750 --anchor center
        ```
        *   **保存路径 (CRITICAL)**: 将裁剪缩放后的三张配套图保存到该表情包输出目录下的 **`assets/` 子目录**中（即 `OUTPUT_DIR/assets/`），**严禁零散放置在外部**。

### Step 4: Final Delivery
Report the complete production results to the user:
1.  **Preview**: Show the generated grid sheet and the matching promotional assets (Banner, Solicitation, Acknowledgment).
2.  **Asset Package**: Provide the absolute clickable link to the consolidated output directory:
    *   Stickers & Assets Project Folder: `OUTPUT_DIR` (Stickers inside the root folder, and Banner/Solicitation/Acknowledgment assets inside the `assets/` subfolder).

## Example Command
> "Generate a set of generic 'Cute Robot' stickers and assets under a single folder."
> "Production line: Make me an office worker set and matching assets for a 'Tired T-Rex'."
