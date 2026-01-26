---
name: wechat-sticker-maker
description: 微信表情包制作工具。自动将六宫格、九宫格、十二宫格的原图裁剪并转换为符合微信表情包规范的格式（表情主图 240x240，聊天页图标 50x50）。
---

# 微信表情包制作工具 (WeChat Sticker Maker)

本 Skill 旨在帮助用户快速将设计好的网格拼图（如六宫格、九宫格、十二宫格）自动裁剪并生成符合微信表情开放平台规范的素材。

## 核心功能

*   **自动裁剪**：支持 2x3, 3x2, 3x3, 3x4, 4x3 等多种网格布局。
*   **智能去底**：支持一键自动移除背景（需开启 `--remove-bg` 参数）。
*   **规范转换**：
    *   **表情主图**：统一调整为 **240x240** 像素 (PNG)。
    *   **聊天页图标**：统一调整为 **50x50** 像素 (PNG)。
*   **含义词生成**：自动生成 `meta.txt` 文件，预留“含义词”填写位置，方便批量管理。
*   **信息模板生成**：自动生成 `info.txt` 文件，包含【表情名称】、【表情介绍】、【一句话简介】的填写模板及字数限制提示。
*   **候选素材生成**：自动提取第1张表情，生成符合规范的【头像/封面图候选】(240x240) 和 【聊天页图标候选】(50x50)。
*   **自动命名**：按照微信规范自动编号 (01, 02, ...)。

## 使用指南

### 1. 准备工作

确保环境中已安装 Python 3 及相关库 (Pillow, rembg)：

```bash
pip install -r skills/wechat-sticker-maker/requirements.txt
```

### 2. 运行脚本

使用 `scripts/make_stickers.py` 对图片进行处理：

```bash
# 自动探测布局并生成
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/your/grid_image.png

# 指定布局 (例如 3行3列)
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png --layout 3x3

# 自动移除背景 (⚠️ 默认关闭，仅在用户明确要求去底时使用)
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png --remove-bg

# 指定输出目录
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png --output ./my_stickers
```

### 3. 输出结果

脚本将在输出目录下生成三个文件夹和更多文件：
*   `main/`: 存放 **表情主图** (240x240)
*   `icon/`: 存放 **表情缩略图标** (50x50, 这里的icon指每张表情的缩略图，非聊天页单一图标)
*   `meta.txt`: **含义词配置表** (格式：`01.png [请输入表情含义]`)
*   `info.txt`: **专辑信息模板** (包含名称、简介模板)
*   `cover_candidate.png`: **封面图候选** (240x240, 取自第1张)
*   `chat_icon_candidate.png`: **聊天页图标候选** (50x50, 取自第1张)

## 规范参考

*   [微信表情制作规范](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/makingSpecifications#specifications_stickers)
