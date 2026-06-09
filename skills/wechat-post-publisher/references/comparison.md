# WeChat Post Publisher Features & Comparison Matrix

## Image-Text Posting (图文)

For short posts with multiple images (up to 9):

```bash
${BUN_X} {baseDir}/scripts/wechat-browser.ts --markdown article.md --images ./images/
${BUN_X} {baseDir}/scripts/wechat-browser.ts --title "标题" --content "内容" --image img.png --submit
```

See [references/image-text-posting.md](references/image-text-posting.md) for details.

## Feature Comparison

| Feature | Image-Text | Article (API) | Article (Browser) |
|---------|------------|---------------|-------------------|
| Plain text input | ✗ | ✓ | ✓ |
| HTML input | ✗ | ✓ | ✓ |
| Markdown input | Title/content | ✓ | ✓ |
| Multiple images | ✓ (up to 9) | ✓ (inline) | ✓ (inline) |
| Themes | ✗ | ✓ | ✓ |
| Auto-generate metadata | ✗ | ✓ | ✓ |
| Default cover fallback (`imgs/cover.png`) | ✗ | ✓ | ✗ |
| Comment control (`need_open_comment`, `only_fans_can_comment`) | ✗ | ✓ | ✗ |
| Requires Chrome | ✓ | ✗ | ✓ |
| Requires API credentials | ✗ | ✓ | ✗ |
| Speed | Medium | Fast | Slow |

## Prerequisites

**For API method**:
- WeChat Official Account API credentials
- Guided setup in Step 2, or manually set in `.super-publisher/.env`

**For Browser method**:
- Google Chrome
- First run: log in to WeChat Official Account (session preserved)

**Config File Locations** (priority order):
1. Environment variables
2. `<cwd>/.super-publisher/.env`
3. `~/.super-publisher/.env`
