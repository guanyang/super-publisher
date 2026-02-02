# GIF Maker (GIF 动画生成助手)

这是一个专为 Agent 流程设计的 Skill，旨在快速将序列帧图片或精灵表（Grid Sprite Sheet）转换为 GIF 动画，并支持针对微信表情包等场景的智能压缩。

## 🧩 核心原理

本 Skill 基于 Python 的 `Pillow` 和 `gifsicle` (可选) 构建，核心处理流程如下：

1.  **灵活的输入源处理 (Input Handling)**:
    *   **序列帧模式**: 自动扫描指定目录下的 `png`/`jpg` 图片，按文件名自然排序作为动画帧。
    *   **精灵表模式**: 支持读取单张大图（如 4x4 网格图），通过 `--layout` 参数将其切分为独立的帧序列。

2.  **动画合成 (Animation Composition)**:
    *   根据用户指定的帧率 (`--fps`)，精确计算每一帧的持续时间。
    *   使用 Pillow 库构建动画，设置循环模式（默认为永久循环）和处理方式（Disposal Method 为 Background，避免透明图层重叠残留）。

3.  **智能压缩 (Smart Compression)**:
    *   (集成 `gifsicle`) 针对微信表情包限制（通常需 <1MB 或 <500KB），提供 `--max-size` 参数。
    *   当输出文件超标时，系统通过二分逼近或预设梯度（Lossy 强度、尺寸缩放）自动尝试压缩，直到文件体积达标，无需人工反复试错。
    *   *注：此功能依赖系统安装 `gifsicle` 工具。*

## 📂 目录结构

Skill 的文件组织结构如下：

```text
skills/gif-maker/
├── README.md               # 本说明文档
├── SKILL.md                # Agent Skill 定义及规范引用
├── requirements.txt        # Python 依赖 (Pillow)
└── scripts/
    ├── make_gif.py         # 核心处理脚本 (包含压缩逻辑)
    └── run.sh              # 自动环境配置与执行入口
```

## 💡 最佳实践

### 配合 WeChat Sticker Maker 使用
通常我们使用 `wechat-sticker-maker` 切分好的静态图序列来生成 GIF：

1.  **切分**: 先用 `wechat-sticker-maker` 将九宫格切分为 `sticker_output/main/` 下的序列图。
2.  **合成**: 再用本 Skill 指向该目录生成 GIF。
    ```bash
    ./skills/gif-maker/scripts/run.sh sticker_output/main/ -o my_anim.gif --fps 10
    ```

### 精灵表直接生成
如果不需要中间的静态图，也可以直接从原图生成：
```bash
# 从 4x4 原图直接生成 25fps 的 GIF
./skills/gif-maker/scripts/run.sh origin_grid.png --layout 4x4 --fps 25 --output direct_anim.gif
```

### 控制体积
为微信表情包制作动画时，务必加上体积限制：
```bash
./skills/gif-maker/scripts/run.sh input_frames/ --max-size 950
```

## 🗣️ 自然语言调用示例

在 Agent 环境中，你可以使用自然语言直接调用此能力：

### 场景一：序列帧合成
**User**: "把 `frame_folder` 文件夹里的图片合成一个 GIF，每秒播放 10 帧。"
**Agent**: (运行脚本 `--fps 10`)

### 场景二：制作表情包动画并压缩
**User**: "用这个 4x4 的图 `motion.png` 做一个 GIF，要做成微信表情包那种，不要超过 1M。"
**Agent**: (运行脚本 `--layout 4x4 --max-size 1000`)

---

## 🛠️ 命令行使用

建议通过 `run.sh` 脚本运行，它会自动管理 Python 虚拟环境：

```bash
# 基础用法
./skills/gif-maker/scripts/run.sh /path/to/frames_dir -o output.gif

# 高级用法 (布局切分 + FPS + 压缩)
./skills/gif-maker/scripts/run.sh /path/to/sheet.png --layout 4x4 --fps 24 --max-size 1024
```
