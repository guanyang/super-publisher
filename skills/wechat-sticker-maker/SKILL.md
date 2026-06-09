---
name: wechat-sticker-maker
description: 微信表情包制作工具。自动将六宫格、九宫格、十二宫格的原图裁剪并转换为符合微信表情包规范的格式（表情主图 240x240，聊天页图标 50x50）。
compatibility: Requires Python 3.9+ and Pillow library.
---

# 微信表情包制作工具 (WeChat Sticker Maker)

本 Skill 旨在帮助用户快速将设计好的网格拼图（如六宫格、九宫格、十二宫格）自动裁剪并生成符合微信表情开放平台规范的素材。

## 核心功能

*   **自动裁剪**：支持 2x3, 3x2, 3x3, 3x4, 4x3 等多种网格布局。
*   **规范转换**：
    *   **表情主图**：统一调整为 **240x240** 像素 (PNG)。
    *   **聊天页图标**：统一调整为 **50x50** 像素 (PNG)。
*   **含义词生成**：自动生成 `meta.txt` 文件，预留“含义词”填写位置，方便批量管理。
*   **信息模板生成**：自动生成 `info.txt` 文件，包含【表情名称】、【表情介绍】、【一句话简介】的填写模板及字数限制提示。
*   **候选素材生成**：自动提取第1张表情，生成符合规范的【头像/封面图候选】(240x240) 和 【聊天页图标候选】(50x50)。
*   **自动命名**：按照微信规范自动编号 (01, 02, ...)。

## 使用指南

### 1. 快速开始 (Quick Start)

无需手动安装依赖，直接运行脚本即可。工具会自动创建虚拟环境 (`.venv`) 并安装所需依赖。

```bash
# 基本用法：自动处理并生成
./skills/wechat-sticker-maker/scripts/run.sh /path/to/your/grid_image.png

# 常用选项：
# - 指定布局 (例如 3x3)
./skills/wechat-sticker-maker/scripts/run.sh /path/to/image.png --layout 3x3

# - 指定输出目录
./skills/wechat-sticker-maker/scripts/run.sh /path/to/image.png --output ./my_stickers
```

### 2. (可选) 手动安装

如果您希望手动管理环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r skills/wechat-sticker-maker/requirements.txt
python3 skills/wechat-sticker-maker/scripts/make_stickers.py ...
```

### 3. 输出结果

脚本将在指定的输出目录下生成两个子文件夹和多个文件。
*   **默认输出路径**：如果用户未指定，默认创建并输出到 `output/stickers_[theme]` 目录（其中 `[theme]` 根据该表情包的具体主题进行替换，如 `output/stickers_cat`）。
*   **自定义输出路径**：用户也可以通过 `--output` 指定自定义输出目录。
*   **输出内容**：
    *   `main/`: 存放 **表情主图** (240x240)
    *   `icon/`: 存放 **表情缩略图标** (50x50, 这里的icon指每张表情的缩略图，非聊天页单一图标)
    *   `meta.txt`: **含义词配置表** (格式：`01.png [请输入表情含义]`)
    *   `info.txt`: **专辑信息模板** (包含名称、简介模板)
    *   `cover_candidate.png`: **封面图候选** (240x240, 取自第1张)
    *   `chat_icon_candidate.png`: **聊天页图标候选** (50x50, 取自第1张)

**输出目录自定义：** Agent 在调用脚本时应传入 `--output` 参数：如果用户指定了路径，则使用用户指定的路径；如果未指定，则默认使用 `output/stickers_[theme]` 格式的路径。生成完毕后，向用户呈报生成在该目录下的具体文件路径与文件预览。

**重要：自动完善元数据 (Meta-Data Auto-Population)**
当运行完本脚本后，Agent **必须**根据所生成的表情包主题、画面内容或所使用的模板，**自动修改并填充** `info.txt` 与 `meta.txt` 中的占位符：
1.  **补充 `info.txt`**：
    *   【表情名称】：结合主题起一个生动的名字（不超过8个汉字，无标点）。
    *   【表情介绍】：描述这套表情包的风格和适用场景（不超过80个汉字）。
    *   【一句话简介】：提炼一个吸睛的宣传语（不超过11个汉字，无标点）。
2.  **补充 `meta.txt`**：
    *   将每一行的 `[请输入表情含义]` 替换为该表情图对应的具体动作或情绪含义（如：`01.png 收到`、`02.png 摸鱼`等，通常为 2-4 个字）。


## 规范参考

*   [微信表情制作规范](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/makingSpecifications#specifications_stickers)
