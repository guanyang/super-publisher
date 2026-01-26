# WeChat Sticker Maker (微信表情包制作助手)

这是一个专为 Agent 流程设计的 Skill，旨在将设计好的网格拼图（如九宫格、六宫格）高效转换为符合[微信表情开放平台](https://sticker.weixin.qq.com/)提交规范的完整素材包。

## 🧩 核心原理

本 Skill 基于 Python 的图像处理库 `Pillow` 构建，核心处理流程如下：

1.  **智能布局探测 (Layout Detection)**:
    *   脚本会根据输入图片的**宽高比 (Aspect Ratio)** 自动推断网格布局。
    *   例如：宽高比接近 1:1 识别为 **3x3 (九宫格)**；接近 2:3 识别为 **3x2 (六宫格)** 等。
    *   也支持通过参数强制指定布局（如 `2x3`, `3x4`）。

2.  **精确切分 (Precision Slicing)**:
    *   根据计算出的行列数，使用浮点数坐标运算，精确地将原图切割为独立的单元格，避免累积误差。

3.  **AI 智能去底 (AI Background Removal)**:
    *   (可选) 集成 `rembg` 库，利用 U2-Net 模型对输入图片进行高精度背景移除，无需手动抠图。

4.  **规范化处理 (Normalization)**:
    *   **主图生成**: 将切片统一缩放至微信要求的 **240x240** 像素，输出为 PNG 格式。
    *   **图标生成**: 同步生成 **50x50** 像素的缩略/聊天页图标。
    *   **候选素材**: 自动提取第一张表情作为“表情专辑封面”和“聊天页图标”的候选图。

4.  **元数据脚手架 (Metadata Scaffolding)**:
    *   自动生成 `meta.txt`: 预填充文件列表，留出“含义词”填写位。
    *   自动生成 `info.txt`: 提供符合字数限制的“名称”、“简介”模板。

## � 目录结构

Skill 的文件组织结构如下：

```text
skills/wechat-sticker-maker/
├── README.md               # 本说明文档
├── SKILL.md                # Agent Skill 定义及规范引用
├── requirements.txt        # Python 依赖 (Pillow)
└── scripts/
    └── make_stickers.py    # 核心处理脚本
```

运行脚本后，生成的**输出目录**结构如下：

```text
sticker_output/
├── cover_candidate.png     # [候选] 专辑封面/头像 (240x240)
├── chat_icon_candidate.png # [候选] 聊天页图标 (50x50)
├── info.txt                # 专辑信息模板 (名称/简介)
├── meta.txt                # 含义词填写表
├── main/                   # 表情主图目录 (01.png, 02.png...)
└── icon/                   # 聊天图标目录 (01.png, 02.png...)
```

## 💡 最佳实践

为了获得最佳的输出效果，建议遵循以下流程：

### 1. 素材准备
*   **源文件**: 建议使用 **透明背景的 PNG** 图片作为输入源。如果源文件是不透明的 JPG，生成的表情包也会带有背景，不仅不美观，还可能不符合“去底”的建议规范。
*   **分辨率**: 尽量保证源图分辨率足够高。例如做一个九宫格（3x3），源图尺寸建议至少为 `720x720` (即每个格子 240x240)，以确保缩放后清晰度。
*   **安全区**: 设计时注意每个格子的主要内容尽量居中，避免贴边，以免视觉上显拥挤。

### 2. 高效工作流
1.  **触发 Skill**: 让 Agent 处理你的网格拼图。
2.  **完善信息**: 打开生成的 `meta.txt`，快速填入每个表情的含义（如“收到”、“谢谢”）。打开 `info.txt` 填入专辑名称和简介。
3.  **最终检查**: 查看 `cover_candidate.png` 和 `chat_icon.png`，如果第一张图不适合做封面，可以手动选择其他生成的图片重命名替换。
4.  **打包上传**: 此时你拥有了上传所需的所有规范素材。

## 🗣️ 自然语言调用示例

在 Agent 环境（如 Claude Code 或 Antigravity）中，你可以使用自然语言直接调用此能力。以下是一些典型的 Prompt 场景：

### 场景一：全自动处理
**User**: "我画了一张九宫格的图 `my_design.png`，帮我把它转换成微信表情包素材。"
**Agent**: (自动识别文件，运行脚本，生成所有素材及 info/meta 文件)

### 场景二：指定布局
**User**: "这个 `funny_cats.jpg` 是一个 2行4列 的拼图，请帮我切分并生成符合微信规范的表情包。"
**Agent**: (调用时补充参数 `--layout 2x4`)

### 场景三：生成及后续指引
**User**: "制作微信表情包需要准备哪些东西？帮我用这张图生成一份草稿。"
**Agent**: (生成素材，并解释生成的 `info.txt` 和 `meta.txt` 用途，指导用户填写含义词)

---

## 🛠️ 命令行使用
如果你希望手动运行脚本：

```bash
# 自动探测布局
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png

# 强制指定布局
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png --layout 3x3

# 启用自动去背 (⚠️ 默认关闭，仅在明确需要时使用)
python3 skills/wechat-sticker-maker/scripts/make_stickers.py /path/to/image.png --remove-bg
```
