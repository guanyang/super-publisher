# GIF Maker

将同一动作的连续PNG/JPG/JPEG/静态WebP或明确布局精灵表制作成GIF，支持透明边缘处理、共享调色板、公共构图和逐帧节奏。原始输入保留，已有输出不会覆盖。

```bash
# 原尺寸连续帧
./skills/gif-maker/scripts/run.sh frames/ -o output/action_v1.gif --fps 8
# 精灵表加工；950KiB为显式制作目标，不代表平台通用限制
./skills/gif-maker/scripts/run.sh motion.png --layout 2x4 --size 240 --anchor bottom -o output/action_v2.gif --max-size 950
# 关键帧复用与停顿
./skills/gif-maker/scripts/run.sh frames/ --sequence 1,2,3,2,1 --durations 80,80,300,80,200 -o output/action_v3.gif
```

流程和检查见[SKILL.md](SKILL.md)，参数、透明处理、静态文字层、切分边界及环境说明见[参数与复核](references/animation-options.md)。成功返回JSON，并生成GIF、同名.animation.json与浅深背景.preview.png；失败退出码为2，不发布失败成品。

run.sh复用满足依赖的技能虚拟环境或当前Python，按需安装Pillow>=10。超限压缩需要gifsicle，压缩保持尺寸和播放时间线；--optimize可选尝试无损优化。直接调用脚本时需自行准备Python依赖。

连续PNG帧可以组成动画；16个独立表情或IP多角度参考图不自动作为动作帧。动画使用统一坐标系与公共裁剪缩放，保留真实位移；提高fps只调整节奏。导出后仍需播放检查IP一致性、动作、首尾衔接和有损画质。

测试：python3 -m unittest discover -s skills/gif-maker/tests -v。
