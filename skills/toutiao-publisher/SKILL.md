---
name: toutiao-publisher
description: Publish articles to Toutiao (Today's Headlines). Handles persistent authentication (login once) and session management. Opens browser for interactive publishing.
compatibility: Requires Python 3.9+, Patchright (Playwright fork), and Google Chrome. Runs in headless mode or launches Chrome for QR code authentication.
---

# Toutiao Publisher Skill

Manage Toutiao (Today's Headlines) account, maintain persistent login session, and publish articles.

## When to Use This Skill

Trigger when user:
- Asks to publish to Toutiao/Today's Headlines
- Wants to manage Toutiao login
- Mentions "toutiao" or "头条号"

## Core Workflow

### Step 1: Authentication (One-Time Setup)

The skill requires a one-time login. The session is persisted for subsequent uses.

```bash
# Browser will open for manual login (scan QR code)
python scripts/run.py auth_manager.py setup
```

**Instructions:**
1.  Run the setup command.
2.  A browser window will open loading the Toutiao login page.
3.  Log in manually (e.g., scan QR code).
4.  Once logged in (redirected to dashboard), the script will save the session and close.

### Step 2: Publish Article

```bash
# Opens browser with authenticated session at publish page
python scripts/run.py publisher.py
```

**Instructions:**
1.  Run the publisher command.
2.  Browser opens directly to the "Publish Article" page.
3.  Write and publish the article manually.
4.  Press `Ctrl+C` in the terminal when done.

> **Note:** Toutiao requires titles to be **2-30 characters**. This tool automatically optimizes titles to fit this constraint (truncating if >30, padding if <2).

#### Advanced Usage (Draft Automation)

You can fill a draft automatically by providing arguments. By default, the tool stops before final publishing so the user can inspect the article and click Publish manually.

```bash
# Fill title, Markdown content, inline images, and cover image
python scripts/run.py publisher.py --title "AI Trends 2025" --content "article.md" --cover "assets/cover.jpg"
```

Markdown images such as `![caption](assets/chart.png)` are inserted into the article body at their original positions. Local relative image paths are resolved from the Markdown file directory.

If the article body contains images, the tool skips explicit cover handling and does not open Toutiao's cover picker. `--cover` is only uploaded when the Markdown body has no inline images.

Debug screenshots are disabled by default. If troubleshooting is needed, add `--debug-screenshots`; screenshots will be saved under `output/toutiao-publisher-debug/` instead of the working directory.

#### Automated Final Publish

Only use this when the user explicitly asks to publish without manual review:

```bash
python scripts/run.py publisher.py --title "AI Trends 2025" --content "article.md" --cover "assets/cover.jpg" --auto-publish
```

Without `--auto-publish`, never click Toutiao's final publish buttons automatically.

### Management

```bash
# Check authentication status
python scripts/run.py auth_manager.py status

# Clear authentication data (logout)
python scripts/run.py auth_manager.py clear
```

## Technical Details

- **Persistent Auth**: Uses `patchright` to launch a persistent browser context. Cookies and storage state are saved to `data/browser_state/state.json`.
- **Anti-Detection**: Uses `patchright`'s stealth features to avoid bot detection.
- **Environment**: Automatically manages a virtual environment (`.venv`) with required dependencies.

## Script Reference

- `scripts/auth_manager.py`: Handles login, session validation, and state persistence.
- `scripts/publisher.py`: Launches authenticated browser for publishing.
- `scripts/run.py`: Wrapper ensuring execution in the correct virtual environment.
