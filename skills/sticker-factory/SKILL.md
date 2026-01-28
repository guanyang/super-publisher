---
name: sticker-factory
description: Automated factory workflow: Generates grid-based sticker sheets (defaulting to Office Worker style but adaptable) and auto-packages them for WeChat using wechat-sticker-maker.
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
        *   **Default**: Load the **Office Worker Template** (`resources/office_worker_template.md`) from the generator skill to fill slots with office memes.
        *   **Custom**: If user specifies a different theme, generate 16 varied actions relevant to that theme satisfying the grid constraints.

*   **Action**:
    *   Call `generate_image` with the constructed prompt.

### Step 2: Auto-Process with Sticker Maker
Once the image is successfully generated, **immediately** trigger the packaging robot.

*   **Command**:
    ```bash
    ./skills/wechat-sticker-maker/scripts/run.sh "PATH_TO_GENERATED_IMAGE" --output "OUTPUT_DIRECTORY" --remove-bg --layout 4x4
    ```
    *   *PATH_TO_GENERATED_IMAGE*: The absolute path returned by the `generate_image` tool.
    *   *OUTPUT_DIRECTORY*: A structured path, e.g., `output/stickers_[theme]_[timestamp]`.

### Step 3: Final Delivery
Report the production results:
1.  **Preview**: Show the generated grid sheet.
2.  **Asset Package**: Provide the path to the processed folder containing:
    *   `main/` (240x240 stickers)
    *   `icon/` (50x50 icons)
    *   `info.txt` & `meta.txt` templates.

## Example Command
> "Generate a set of generic 'Cute Robot' stickers."
> "Production line: Make me an office worker set for a 'Tired T-Rex'."
