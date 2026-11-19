# 导出与审片

## 清单与导出

在项目工作目录保存 `pack.json`。素材路径相对清单，也可用绝对路径。`reference` 可记录角色参考供后续生成复用，导出只读取动作素材。

```json
{
  "reference": "character.png",
  "size": 320,
  "font": "fonts/Chinese-Bold.ttf",
  "stickers": [
    {"name": "收到", "gif": "sample/gifs/收到.gif"},
    {
      "name": "马上来",
      "caption": "马上来",
      "source": "on-my-way.png",
      "layout": "2x2",
      "sequence": [1, 2, 3, 4],
      "durations_ms": [150, 130, 150, 130]
    }
  ]
}
```

```bash
python3 <skill-dir>/scripts/build_pack.py --spec pack.json --output output/office-v1 --zip
```

- `source` 可填同尺寸连续帧目录，也可填精灵表，并用 `layout` 指定行×列。帧号从 1 开始，目录按文件名自然排序，精灵表按行读取；`durations_ms` 对应实际播放顺序。省略时序时顺序播放，默认 12 fps。
- 文案有需要时用 `caption` 和共同的本地 `font`，字体集合可加 `font_index`。用同尺寸已对齐帧时，预先在底部留出文字区域。源帧已有文字或需要无字时省略 `caption`。
- 修改一条时，修改项用 `source` 和新的时序，其余项用 `{"name":"条目名","gif":"上一版/gifs/条目名.gif"}`。`gif` 逐字节复用，仍检查透明度、尺寸和循环。输出选新目录，ZIP 只含 GIF；样片可省略 `--zip`。
- 默认 320 方图、透明循环。实底素材用 `transparent: false`，体积上限用 `max_kib`。精确尺寸构图直接用同尺寸帧，避免帧间漂移。GIF 采用二值透明，要求保留半透明边缘时可从原始 RGBA 帧另导 APNG。

运行环境为 Python 3.9+ 与 Pillow 10+。仓库版的批量入口直接复用同级 `gif-maker` 目录里的编码程序。

## 用实际导出文件看片

`review.html` 默认显示从实际 GIF 解码的最长停留帧，可播放原 GIF 并切换深浅底。比较两个已有版本时，可用 `python3 <skill-dir>/scripts/build_review.py --output review.html v1.gif v2.gif` 按给定顺序排片。看片时检查角色一致性、裁切、残影和末帧接首帧，结合小图确认文字可读。
