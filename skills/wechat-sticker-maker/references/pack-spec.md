# pack.json：单一制作说明

所有输入路径相对pack.json所在目录解析，也可用绝对路径。明确保留已确认的角色和动作；不要靠脚本猜文案、版权或图标裁剪范围。

```json
{
  "album": {
    "name": "河狸打工日常",
    "description": "差不多小河狸陪你摸鱼赶工等下班",
    "copyright": "用户提供的署名",
    "tagline": "上班凑合下班复活"
  },
  "character": {
    "reference": "character.png",
    "invariants": ["同一颗微歪门牙", "棕色毛发", "宽扁尾巴"],
    "style": "真实立体毛发"
  },
  "grid": "grid.png",
  "layout": "4x4",
  "caption_mode": "render",
  "font": "/absolute/path/to/chinese-font.ttc",
  "items": [
    {"id": 1, "caption": "开机失败", "action": "趴在笔记本上", "prop": "笔记本"}
  ],
  "assets": {
    "cover": {"source": "cover-without-text.png"},
    "chat_icon": {"source": "character.png", "crop": [20, 10, 180, 170]},
    "banner": {"source": "banner-original.png"},
    "reward_guide": {"source": "reward-guide-original.png"},
    "reward_thanks": {"source": "reward-thanks-original.png"}
  }
}
```

上例只展示一个item的结构，实际整包必须填写id=1至16共16项。name/description必填；copyright/tagline可省略。name≤8、description≤80、copyright≤10来自用户提供的页面截图；tagline≤11为旧制作约定，不代表当前页面必填。

- `caption_mode=render`：输入网格无字，通过指定字体加字；中文字体由本机提供，不能使用示例占位路径。脚本记录字体路径，不复制字体文件。
- `caption_mode=baked`：输入网格已含正确文案，不再加字。
- `caption_mode=none`：输出无字表情，items.caption仍用于meta.txt。
- `boundaries`可选：`{"x":[0,319,644,938,1254],"y":[0,316,626,929,1254]}`。这是小河狸办公原图的坐标示例，不能照搬给其他尺寸。
- `assets`在预览阶段可以省略。整包需要cover/chat_icon/banner；赞赏两张可同时省略，提供则成对。
- `crop`是源图上的整数像素框，不包含文字，不越界。不要把一张带字图中所有alpha像素都当作角色头部。

## 可选的情绪字体与排版

旧配置中的`font`仍可作为`regular`字体使用。需要多字体时添加`fonts`，需要整套默认样式时添加`typography`，逐张差异放在`items[].typography`。这些选项仅用于`caption_mode=render`，不改变角色源图。设计取舍见[排版参考](typography.md)。

```json
{
  "fonts": {
    "regular": {"path": "/absolute/path/to/main-font.ttc", "index": 0},
    "handwritten": {"path": "/absolute/path/to/hand-font.ttc", "index": 2},
    "rounded": "/absolute/path/to/round-font.ttf"
  },
  "typography": {
    "font_role": "regular", "font_size": 23, "layout": "bottom",
    "angle": 0, "fill": "#563323", "stroke_fill": "#fff3dc", "stroke_width": 1.5
  },
  "items": [
    {"id": 1, "caption": "又要报销", "typography": {"font_role": "handwritten"}},
    {"id": 2, "caption": "免打扰", "typography": {"font_role": "rounded", "layout": "arc_top"}},
    {"id": 3, "caption": "我撤回了", "typography": {"layout": "top", "angle": 4}}
  ]
}
```

这是需要合并到完整制作说明的字段片段，仍需16个条目。字体角色名可自定；路径相对pack.json解析。`fonts.regular`存在时优先于旧`font`；index省略为0，TTC索引须在本机核对，示例2并不通用于所有字体。缺字、缺失角色或无效索引会停止构建，不自动替换。

`font_size`和`stroke_width`以最终主图像素为单位，字号至少12px。默认23px；空间不足时仅向下适配至18px，明确指定小于18px时不再向下缩。文字层含旋转和描边的高度不超过画布18%，过长则失败，需缩短文案或重新安排。`angle`单位为度，支持-15至15，正值逆时针。布局支持`bottom`、`top`、`arc_top`；配色和描边字段如例。未提供字段继承整套设置，再继承脚本默认值。

可选命令：`build_pack.py --spec pack.json --output output/type_compare_v1 --preview-only --compare-typography`。额外生成统一默认字体下置版A与配置版B的`comparison.png`，不创建额外主图或ZIP。完整构建也可使用该对照开关，配套素材要求保持不变。实际字体名称、路径、索引、适配字号和边界写入manifest.json；导出的pack.json将字体路径转成绝对路径以支持本机复建，不分发字体文件。

## 输出与重跑

预览输出main/、thumbnail/、icon/、原始切片、透明grid.png、浅深背景preview.png、文案和本地检查清单，不加工配套图或生成ZIP。确认后使用原始制作说明补齐assets，并输出到新的完整版本目录。

完整输出另含assets/及相邻的`目录名.zip`。原图保存在source/，所有处理从原图开始。已有目录或ZIP不会被覆盖；同一份说明可重复构建到不同版本目录，不能让旧版本残留混入。

pack.json中的reference、style、invariants、action和prop用于技能创作与复核；脚本不会根据这些文字自动调用生图，也不会宣称已验证角色一致性或表意准确性。
