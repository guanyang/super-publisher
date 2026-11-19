# 导出、审片与打包

微信开放平台帮助中心的静态封面图规格为 957 × 1278 像素，支持 PNG、JPG 和 JPEG，体积上限 500 KB，建议 sRGB。脚本用 500,000 字节作为保守上限，导出带 sRGB 配置的 JPEG。规格有变动时以实际提交页为准。[微信红包封面开放平台 · 制作规范](https://cover.weixin.qq.com/cgi-bin/mmcover-bin/readtemplate?t=page/index#/doc?page=design#%E5%88%B6%E4%BD%9C%E8%A7%84%E8%8C%83)

```bash
python3 <skill-dir>/scripts/build_cover.py artwork.png --output output/cover-v1
python3 <skill-dir>/scripts/build_cover.py artwork.png --focus 0.64 0.43 \
  --preview-only --output output/cover-crop-v2
```

- 使用 Python 3.9+ 和 Pillow 10+。缺少 Pillow 时可在所用 Python 环境安装技能目录的 `requirements.txt`。
- `--focus X Y` 用原图的归一化坐标，`0 0` 为左上，`1 1` 为右下。裁切框尽量以焦点为中心并保持在原图内。默认居中，按比例裁切，避免拉伸。若多个关键元素在原比例下无法同时保留，回到原画调整构图或补画背景。
- 有可见透明区域的源图需要给出预期底色，例如 `--background '#551e2b'`。完整原画保留在原路径，重导使用新输出目录。
- 默认生成 `cover.jpg` 和离线 `review.html`。只需审片时传 `--preview-only`，生成 `review.html` 和 `preview.jpg`。审片页引用同目录的一张 JPEG，分享或打包时将两者放在一起。命令返回实际尺寸、字节数、裁切范围与输出路径。

审片页第一幅核对主体有无被裁切，第二幅用辅助区检查潜在遮挡，第三幅检查缩小后的辨识度。遮挡辅助区是构图示意，实际场景的裁剪和文字露出在平台手机预览中核验。出图前还要读一遍画面文案，确认文字、尺寸和文件符合这次交付要求。

提交前在平台预览发红包页、红包气泡、拆红包页和红包详情页，按需要调整气泡露出的画面。优先使用原创或已获授权的素材，涉及真实肖像时按平台要求准备证明，封面以装饰和祝福为主。[微信红包封面开放平台 · 设计原则](https://cover.weixin.qq.com/cgi-bin/mmcover-bin/readtemplate?t=page/index#/doc?page=design#%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99)

## 从预览打包

```bash
python3 <skill-dir>/scripts/pack_cover.py output/cover-crop-v2 \
  --output output/cover-pack-v2 --source artwork.png
```

输入为包含 `review.html` 和 `preview.jpg` 的预览目录。脚本复核封面和目录中已有的挂件，原样复制上传素材，保留审片版式并更新图片名。`--source` 可重复传入，只有指定的源文件会进入 `sources/`。输出目录含上传素材、可离线打开的审片页和 `cover-pack.zip`。解压后打开 `review.html` 查看整包。
