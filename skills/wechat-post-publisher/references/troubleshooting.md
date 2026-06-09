# WeChat Post Publisher Troubleshooting Guide

## Pre-flight Check (Optional)

Before first use, suggest running the environment check. User can skip if they prefer.

```bash
${BUN_X} {baseDir}/scripts/check-permissions.ts
```

Checks: Chrome, profile isolation, Bun, Accessibility, clipboard, paste keystroke, API credentials, Chrome conflicts.

**If any check fails**, provide fix guidance per item:

| Check | Fix |
|-------|-----|
| Chrome | Install Chrome or set `WECHAT_BROWSER_CHROME_PATH` env var |
| Profile dir | Shared profile at `super-publisher/chrome-profile` (see CLAUDE.md Chrome Profile section) |
| Bun runtime | `brew install oven-sh/bun/bun` (macOS) or `npm install -g bun` |
| Accessibility (macOS) | System Settings → Privacy & Security → Accessibility → enable terminal app |
| Clipboard copy | Ensure Swift/AppKit available (macOS Xcode CLI tools: `xcode-select --install`) |
| Paste keystroke (macOS) | Same as Accessibility fix above |
| Paste keystroke (Linux) | Install `xdotool` (X11) or `ydotool` (Wayland) |
| API credentials | Follow guided setup in Step 2, or manually set in `.super-publisher/.env` |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing API credentials | Follow guided setup in Step 2 of the main workflow |
| Access token error | Check if API credentials are valid and not expired |
| Not logged in (browser) | First run opens browser - scan QR to log in |
| Chrome not found | Set `WECHAT_BROWSER_CHROME_PATH` env var |
| Title/summary missing | Use auto-generation or provide manually |
| No cover image | Add frontmatter cover or place `imgs/cover.png` in article directory |
| Wrong comment defaults | Check `EXTEND.md` keys `need_open_comment` and `only_fans_can_comment` |
| Paste fails | Check system clipboard permissions |
