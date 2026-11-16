# 微信表情配套素材

继承已确认角色和画风，独立生成横幅及可选的赞赏引导、致谢场景。尺寸和背景约定见[SKILL.md](SKILL.md)，示例赞赏文案可替换，不称为强制官方文案。

```bash
python3 skills/wechat-sticker-assets-designer/scripts/crop_and_resize.py banner-original.png \
  --width 750 --height 400 --anchor center --output output/banner.png --max-bytes 512000
```

原图不被覆盖。省略output时生成`原文件名-宽x高.png`。宽高比不符时按anchor裁剪，保持比例；输出存在时停止。压缩先无损，再对不透明图尝试带抖动调色板，不能通过缩小像素尺寸达标。

完整素材包由[制作入口](../wechat-sticker-maker/SKILL.md)调用本脚本；保留配套原图，压缩后复查文字、色带和毛发。上传限制以当前平台页面为准。
