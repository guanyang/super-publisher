# AI 图生视频与口播指南 (AI Image-to-Video Guide)

本手册专注于指导如何使用 AI 工具（如 Runway, Luma, Gemini/Veo, Kling/海螺）将静态图片转化为动态视频，并实现人物角色的“开口说话”与情感表达。

## 1. 核心逻辑：从静态到动态

与文生图不同，图生视频的 Prompt 重点在于描述**动作 (Motion)** 和 **运镜 (Camera)**，而非画面细节。

### 视频万能公式 (The Motion Formula)

> **`[主体动作] + [环境动态] + [摄像机运镜] + [光影/氛围变化] + [物理特性/特效]`**

| 模块 | 关键词示例 (Prompt) | 作用 |
| :--- | :--- | :--- |
| **主体动作 (Subject)** | The cat blinks and yawns (眨眼打哈欠), Hair blowing (头发飘动), Walking forward | 让主角“活”过来 |
| **环境动态 (Env)** | Clouds moving fast (云流), Rain falling (雨), Water rippling (水波) | 增加背景生气 |
| **运镜 (Camera)** | **Zoom In/Out** (推拉), **Pan Left/Right** (摇镜), **Orbit** (环绕), **Static** (固定镜头) | 引导观众视线 |
| **特效 (Effects)** | Slow motion (慢动作), Time-lapse (延时), Motion blur (动态模糊) | 增加质感 |
| **比例 (Aspect Ratio)** | **--ar 9:16** (竖屏/抖音), **--ar 16:9** (横屏/电影) | 适配播放平台 |

---

## 2. 数字人口播专用方案 (Talking Head / Narrator)

如果你想让图片中的角色（如猫、数字人）开口讲解知识或灌输鸡汤，请遵循以下策略。

### 提示词公式 (The Narrator Formula)
> **`[面部特写/眼神接触] + [微表情描述] + [说话动作/手势] + [情绪氛围] + [Static Camera]`**

*   **关键点**：使用 `Static camera` (固定镜头) 防止背景乱晃，专注于面部；使用 `Lip Sync` (口型同步) 指令配合音频。

### 懒人生成器指令
复制以下指令给 AI，快速生成配套的视频提示词和口播文案：

```markdown
# Role: AI Video Content Director

我有一张【人物/角色图片】，想制作一段【心灵鸡汤/专业讲解】视频。请完成：

**任务一：编写图生视频 Prompt (Visual)**
*   英文提示词，专注于人物自然开口说话、眼神交流。
*   包含细腻的微表情描述 (Micro-expressions)。
*   结构：`[Character talking] + [Expressions] + [Gestures] + [Static Camera] --ar 9:16`
*   **注意**：默认添加 `--ar 9:16` 参数以生成竖屏视频。

**任务二：撰写短视频口播文案 (Script)**
*   中文文案，时长 15-30 秒。
*   风格：[指定风格]。
*   结构：黄金开头 (0-3s) -> 共鸣/干货 -> 结尾金句。
```

---

## 3. 实战案例：治愈系学者猫

**场景目标**：让一只戴眼镜的猫开口说话，安抚深夜焦虑的用户。

### 视觉提示词 (Visual Prompt)
可以直接复制到 Runway Gen-3 / Luma / Gemini Veo 中使用：

```text
Use this image as a reference. Generate a high-quality video of this cat talking.

Action: The cat should look gentle, nod slightly, and move its mouth naturally as if speaking deep wisdom. Avoid exaggerated movements.

Dialogue (Lip Sync): "嘿，别担心今晚。你的焦虑只是因为你对未来有更多的期待。现在好好休息吧，明天的太阳会为你照常升起。"

Audio: Use a warm, soothing male voice speaking Mandarin Chinese.

Aspect Ratio: --ar 9:16
```

### 口播脚本 (Script) - 20s 版本
如果工具不支持一次生成 20s，请按以下分段生成并拼接：

*   **片段 1 (0-7s)**:
    *   *文案*: "嘿，还没睡吗？是不是脑子里又在开深夜研讨会了？"
    *   *画面*: 猫咪直视镜头，微微歪头，眼神关切。
*   **片段 2 (7-14s)**:
    *   *文案*: "别担心，那不是你的错。你的焦虑，其实是你对更好未来的期待。"
    *   *画面*: 猫咪低头看书后抬起头，眼神坚定温柔。
*   **片段 3 (14-20s)**:
    *   *文案*: "哪怕慢一点，只要还在呼吸，就是在积蓄力量。晚安。"
    *   *画面*: 猫咪缓慢眨眼，最后微笑，画面渐暗 (Fade out)。

---

## 4. 工具能力速查表 (截至 2026.01)

| 工具名称 | 核心优势 | 图生视频 | 口型同步 (Lip Sync) | 中文支持 |
| :--- | :--- | :--- | :--- | :--- |
| **Runway Gen-3 Alpha** | 综合画质最强，运镜控制精准 | ✅ | ✅ (强) | ⭐️⭐️⭐️ |
| **Hailuo (海螺 AI)** | **中文语义理解最好**，生成速度快 | ✅ | ✅ (强) | ⭐️⭐️⭐️⭐️⭐️ |
| **Luma Dream Machine** | 动态幅度大，适合大动作视频 | ✅ | ⚠️ (一般) | ⭐️⭐️ |
| **Gemini / Veo 3** | 多模态理解力强，支持长文本Prompt | ✅ | ✅ (集成中) | ⭐️⭐️⭐️⭐️ |
| **Kling (可灵)** | 视频时长长 (最长可达 2mins) | ✅ | ⚠️ (一般) | ⭐️⭐️⭐️⭐️ |

### 专家建议 (Pro Tips)
1.  **竖屏优先**：短视频平台（TikTok/抖音/Shorts）默认使用 **`--ar 9:16`**。如果原图是横屏，AI 会尝试裁切或填充，建议输入图片时本身就是 9:16 比例。
2.  **分段生成**：目前主流模型的黄金时长在 5-10 秒。长视频务必拆解脚本，分段生成后在剪辑软件中拼接。
3.  **音画分离**：如果模型生成的中文口音不自然，建议只生成“说话的动作 (Talking motion without audio)”，然后使用剪映/TTS生成配音，后期对齐。
4.  **固定镜头**：口播类视频切忌镜头乱晃。Prompt 中务必加上 `Static camera` 或 `Slow push in`。
