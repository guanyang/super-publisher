# AI 文生图提示词指南 (AI Image Generation Guide)

本手册旨在提供一套通用的 AI 绘画提示词构建框架，帮助你快速生成高质量的 AI 图像。无论使用 Midjourney、Stable Diffusion 还是 DALL-E，这套逻辑都适用。

## 1. 万能提示词公式 (The Master Formula)

高质量的提示词通常遵循以下结构，建议按顺序组合：

> **`[主体描述] + [艺术风格/媒介] + [环境/背景] + [光影/氛围] + [构图/视角] + [画质/修饰词]`**

### 模块详解

| 模块 | 说明 | 关键词示例 (英/中) |
| :--- | :--- | :--- |
| **主体 (Subject)** | 画面核心内容 | Cyberpunk girl (赛博朋克少女), Floating island (漂浮岛屿), A cat wearing glasses (戴眼镜的猫) |
| **风格 (Style)** | 决定画面质感 | **写实**: Photorealistic, 8k, Unreal Engine 5<br>**插画**: Oil painting (油画), Watercolor (水彩), Ukiyo-e (浮世绘), Anime (日漫)<br>**3D**: 3D Render, Blender, Octane Render, Clay material (粘土材质) |
| **环境 (Environment)** | 交代场景 | Neon street (霓虹街道), Ancient forest (原始森林), Minimalist white room (极简白屋), Space station (太空站) |
| **光影 (Lighting)** | 营造氛围 | Cinematic lighting (电影布光), Soft light (柔光), Rim light (侧逆光), Volumetric lighting (体积光/丁达尔效应) |
| **构图 (Composition)** | 镜头语言 | Extreme close-up (大特写), Wide angle (广角), Bird's-eye view (鸟瞰), Symmetrical (对称), Depth of field (景深) |
| **色调 (Color)** | 色彩倾向 | Pastel colors (柔和粉彩), Black and gold (黑金), Vibrant (鲜艳), Monochrome (单色), Vaporwave (蒸汽波) |

---

## 2. 懒人生成器指令 (AI Generator Prompt)

如果你不想手动拼接，可以将以下指令复制给任何 AI 助手（如 ChatGPT/Claude/Gemini），让它帮你写：

```markdown
# Role: AI Image Prompt Expert

请作为一名专业的 Midjourney/Stable Diffusion 提示词工程师。我将给你一个【主题】和一个【风格】，请你按照以下结构为我编写 3 个不同变体的英文提示词：

**结构公式：**
`[Subject/Action] + [Art Style/Medium] + [Environment] + [Lighting/Color] + [Camera/Composition] + [Quality Tags]`

**要求：**
1. 提示词必须是**英文**。
2. 包含丰富的形容词和细节描述。
3. 针对每个变体，在末尾加上适当的参数（如 --ar 16:9 --v 6.0 --stylize 250）。
4. 在每个提示词下方附带中文的简短设计意图说明。

---
现在，请等待我输入【主题】和【风格】。
```

---

## 3. 实战案例库

### 案例一：戴眼镜的猫 (Cat with Glasses)

**推荐风格：皮克斯/迪士尼 3D 动画风格 (Pixar/Disney 3D Animation)**
*特点：拟人化神态生动，毛发质感强，色彩讨喜。*

#### 方案 A：呆萌学者风 (3D Pixar Style)
> **Prompt:** A cute fluffy ginger cat wearing oversized round black-rimmed glasses, sitting on a pile of colorful hardcover books, holding a small reading lamp. Style: 3D playful character render, Pixar movie style, Unreal Engine 5, C4D, clay texture. Environment: A cozy warm library with floating dust particles. Lighting: Soft cinematic volumetric lighting, warm golden hour sunbeams. Composition: Low angle close-up, depth of field blurring the background. --ar 3:4 --stylize 250 --v 6.0

#### 方案 B：赛博朋克未来风 (Cyberpunk Neon)
> **Prompt:** A sleek black cat wearing futuristic glowing neon visor glasses, reflecting the city lights. Style: Cyberpunk aesthetics, hyper-realistic photography, high-tech sci-fi atmosphere. Environment: Rainy futuristic Tokyo street at night, wet ground reflections. Lighting: Dramatic contrasting teal and magenta neon lighting, rim light. Details: 8k resolution, highly detailed fur texture, insane details. --ar 16:9 --v 6.0

#### 方案 C：复古油画贵族风 (Vintage Oil Painting)
> **Prompt:** Portrait of a British Shorthair cat wearing a gold monocle and a vintage Victorian suit with a bow tie. Style: Classic oil painting, Renaissance art style, heavy brushstrokes, rich textures. Environment: Dark textured vintage background. Lighting: Rembrandt lighting, dramatic chiaroscuro, moody shadows. Composition: Symmetrical front view portrait, elegant and regal pose. --ar 2:3 --v 6.0

### 案例二：喝咖啡的程序员 (Programmer with Coffee)

#### 方案 A：电影感写实风格 (Cinematic Realistic)
> **Prompt:** A young programmer sitting at a cluttered wooden desk with multiple monitors displaying code, holding a steaming cup of coffee, looking tired but focused. Style: Hyper-realistic, Cinematic photography, shot on 35mm lens. Lighting: Warm desk lamp lighting contrasting with cool blue moonlight from the window, moody atmosphere, volumetric lighting. Details: 8k resolution, highly detailed texture, unreal engine 5 render. --ar 16:9 --v 6.0

#### 方案 B：皮克斯/3D 盲盒风格 (3D CUTE / Pixar Style)
> **Prompt:** A cute chibi character of a programmer, oversized glasses, hoodie, typing on a small keyboard, a giant coffee mug next to them. Style: 3D rendering, Blender style, Clay material, C4D, Pop mark style. Lighting: Bright studio lighting, soft shadows, pastel color palette (soft blue and orange). Composition: Isometric view, clean background. --ar 1:1 --niji 6

---

## 4. 常用参数速查 (Midjourney 为例)

*   `--ar [宽:高]`: 设置图片比例 (Aspect Ratio)。
    *   `--ar 16:9`: 电脑壁纸/电影感
    *   `--ar 9:16`: 手机壁纸/海报
    *   `--ar 1:1`: 头像/Instagram
    *   `--ar 4:3`: 传统照片
*   `--v [版本号]`: 模型版本，目前常用 `6.0` 或 `5.2`。
*   `--niji [版本号]`: 专门针对二次元/动漫风格的模型 (如 `--niji 6`)。
*   `--stylize [数值]`: 风格化程度 (0-1000)，数值越高越艺术，越低越忠实于 Prompt。默认为 100。
