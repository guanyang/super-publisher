---
name: wechat-post-publisher
description: Posts content to WeChat Official Account (微信公众号) via API or Chrome CDP. Supports article posting (文章) and image-text posting (贴图).
version: 1.56.1
compatibility: Requires Bun runtime (or npx), Google Chrome (for browser mode), and macOS Accessibility permissions (if using browser automation on macOS).
metadata:
  openclaw:
    homepage: https://github.com/guanyang/super-publisher#wechat-post-publisher
    requires:
      anyBins:
        - bun
        - npx
---

# Post to WeChat Official Account

## Language

**Match user's language**: Respond in the same language the user uses. If user writes in Chinese, respond in Chinese. If user writes in English, respond in English.

## Script Directory

**Agent Execution**: Determine this SKILL.md directory as `{baseDir}`, then use `{baseDir}/scripts/<name>.ts`. Resolve `${BUN_X}` runtime: if `bun` installed → `bun`; if `npx` available → `npx -y bun`; else suggest installing bun.

| Script | Purpose |
|--------|---------|
| `scripts/wechat-browser.ts` | Image-text posts (图文) |
| `scripts/wechat-article.ts` | Article posting via browser (文章) |
| `scripts/wechat-api.ts` | Article posting via API (文章) |
| `scripts/md-to-wechat.ts` | Markdown → WeChat-ready HTML with image placeholders |
| `scripts/check-permissions.ts` | Verify environment & permissions |

## Reference Guides

For detailed setup, configuration, features, and troubleshooting, refer to these standalone documents:
*   [Multi-Account & EXTEND.md Configuration](references/accounts.md)
*   [Feature Comparison Matrix & Prerequisites](references/comparison.md)
*   [Environment Pre-flight Check & Troubleshooting](references/troubleshooting.md)

---

## Article Posting Workflow (文章)

Copy this checklist and check off items as you complete them:

```
Publishing Progress:
- [ ] Step 0: Load preferences (EXTEND.md)
- [ ] Step 0.5: Resolve account (multi-account only - see references/accounts.md)
- [ ] Step 1: Determine input type
- [ ] Step 2: Select method and configure credentials
- [ ] Step 3: Resolve theme/color and validate metadata
- [ ] Step 4: Publish to WeChat
- [ ] Step 5: Report completion
```

### Step 0: Load Preferences
Check and load `EXTEND.md` settings (details in [Preferences & Multi-Account Settings](references/accounts.md)). If not found, complete first-time setup BEFORE any other steps.
Resolve: `default_theme` (default `default`), `default_color`, `default_author`, `need_open_comment` (default `1`), `only_fans_can_comment` (default `0`).

### Step 1: Determine Input Type
*   **HTML file**: Ends with `.html`, file exists -> Skip to Step 3.
*   **Markdown file**: Ends with `.md`, file exists -> Continue to Step 2.
*   **Plain text**: Otherwise -> Save to `post-to-wechat/yyyy-MM-dd/[slug].md` (generate slug from first 2-4 English words of content), then continue to Step 2.

### Step 2: Select Publishing Method and Configure
Ask publishing method (unless specified in `EXTEND.md` or CLI):
*   `api` (Recommended, Fast, requires API credentials)
*   `browser` (Slow, requires Chrome, login session)

If API Selected, check credentials in `.super-publisher/.env` or `~/.super-publisher/.env`. If missing, guide user to obtain AppID/AppSecret from WeChat Admin platform and save.

### Step 3: Resolve Theme/Color and Validate Metadata
1.  **Resolve Theme & Color**: From CLI -> EXTEND.md defaults -> Fallback (`default`).
2.  **Validate Metadata**:
    *   `Title`: Prompt or auto-generate from first H1/H2 or first sentence.
    *   `Summary`: Use `description`/`summary` in frontmatter, or prompt, or auto-generate (first paragraph truncated to 120 chars).
    *   `Author`: CLI `--author` -> frontmatter `author` -> `default_author`.
    *   `Cover Image`: Check CLI `--cover` -> frontmatter cover keys -> default `imgs/cover.png` -> first inline image. (Stop and request if missing for API).

### Step 4: Publish to WeChat
*   **CRITICAL**: Pass the original markdown file directly, do NOT pre-convert to HTML.
*   **API Method**:
    ```bash
    ${BUN_X} {baseDir}/scripts/wechat-api.ts <file> --theme <theme> [--color <color>] [--title <title>] [--summary <summary>] [--author <author>] [--cover <cover_path>] [--no-cite]
    ```
*   **Browser Method**:
    ```bash
    ${BUN_X} {baseDir}/scripts/wechat-article.ts --markdown <markdown_file> --theme <theme> [--color <color>] [--no-cite]
    # OR
    ${BUN_X} {baseDir}/scripts/wechat-article.ts --html <html_file>
    ```

### Step 5: Completion Report
Print status details: Input path, Method, Theme/Color, Title, Summary, Images count, Comment settings, and Resulting draft links or IDs. See [Features & Comparison Matrix](references/comparison.md) for more details.
