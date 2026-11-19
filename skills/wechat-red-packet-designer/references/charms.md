# 静态挂件

封面挂件用于拆红包页，气泡挂件用于聊天中的红包气泡。两个图层各自选填。用有造型的装饰图案延续封面主题，例如把封面的梅花做成一簇小枝，给红包轮廓留出辨识空间。平台上传后会分别和封面图合成。[微信红包封面开放平台 · 制作规范](https://cover.weixin.qq.com/cgi-bin/mmcover-bin/readtemplate?t=page/index#/doc?page=design#%E5%88%B6%E4%BD%9C%E8%A7%84%E8%8C%83)

| 素材 | 画布 | 格式和体积 | 模板避让区 |
| --- | --- | --- | --- |
| 封面挂件 | 1053 × 1746 px | PNG，≤ 300 KB | `96 ≤ x < 957` 且 `342 ≤ y < 1650` 的矩形 |
| 气泡挂件 | 480 × 384 px | PNG，≤ 300 KB | 整个宽度，`96 ≤ y < 312` 的横带 |

坐标从画布左上角的 `(0, 0)` 起算。避让区取自官方 2026-01-14 Sketch 设计模板。区内保持全透明，包括边缘的半透明像素。脚本以 300,000 字节为保守上限，无损保存透明 RGBA，并写入建议的 sRGB 配置。[下载微信官方设计模板](https://weixinredpacket.wxqcloud.qq.com/design_template/20260114/%E7%BA%A2%E5%8C%85%E5%B0%81%E9%9D%A2%E8%AE%BE%E8%AE%A1%E6%A8%A1%E6%9D%BF.zip)

已有按模板摆放好的 PNG 时，传 `--cover-charm` 或 `--bubble-charm`。还未摆放时，用相应的 `--*-charm-box X Y W H` 指定目标框。脚本取可见主体轮廓并留边，按比例缩放并居中放入框中。取框时排除外围低透明度散点，保留框内 alpha，导出时仍逐像素检查避让区。有意保留远处柔光或低透明装饰时，可先按模板摆好再传入。

```bash
python3 <skill-dir>/scripts/build_cover.py artwork.png --output output/cover-v2 \
  --cover-charm branch.png --cover-charm-box 740 54 250 225 \
  --bubble-charm flower.png --bubble-charm-box 332 6 110 80 --bubble-focus-y 0.54
```

输出所选挂件的 `cover-charm.png`、`bubble-charm.png`，审片页会显示对应的合成示意和带避让标记的透明层。封面挂件有完整和缩小两种视图。气泡裁切的纵向位置用 `--bubble-focus-y` 调节，默认 `0.5`，`0` 靠上，`1` 靠下。预览模式使用带 `-preview` 后缀的 PNG。素材超限时，先减少纹理或缩小图案在画布上的占用，再导出同尺寸透明 PNG。最终合成效果在微信平台手机预览中核对。
