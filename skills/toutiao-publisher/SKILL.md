---
name: toutiao-publisher
description: Publish or prepare articles for Toutiao/头条号, check or restore shared login state, fill Markdown drafts with inline images and covers, and optionally complete final publishing. Use for requests such as 发布到头条、检查头条登录、填充头条草稿、上传图文、人工审核 or explicitly authorized automatic publishing.
---

# Toutiao Publisher

Use the scripts from this Skill directory. Resolve the directory containing this
`SKILL.md` first and set its absolute path as `SKILL_DIR`; do not assume the caller's
working directory is the Skill directory.

## Safety rules

- Default to `--mode manual`. Leave Chrome open for the user to review and click Publish.
- Use `--mode auto` only when the user explicitly authorizes final publishing.
- Run `clear --yes` or `reauth --yes` only after the user confirms that all local
  Agents may lose the shared Toutiao session.
- Do not bypass input validation or treat an unconfirmed publish click as success.

## Preflight authentication

Check the protected Toutiao page before asking the user to scan a QR code:

```bash
python3 "$SKILL_DIR/scripts/run.py" auth_manager.py status --verify --json
```

If the result status is `not_authenticated`, open the interactive login flow:

```bash
python3 "$SKILL_DIR/scripts/run.py" auth_manager.py setup --json
```

The shared profile lives under `~/.super-publisher/toutiao-publisher/` by default.
Codex, Kiro, Antigravity, and direct CLI runs by the same system user reuse it.
Set `SUPER_PUBLISHER_DATA_DIR` to override the location; relative values resolve
from the user home directory.

## Prepare and publish an article

Validate inputs without opening Chrome:

```bash
python3 "$SKILL_DIR/scripts/run.py" publisher.py \
  --mode validate \
  --title "AI Trends 2026" \
  --content-file "/absolute/path/article.md" \
  --cover "/absolute/path/cover.jpg" \
  --json
```

After validation succeeds, fill the draft and wait for manual review:

```bash
python3 "$SKILL_DIR/scripts/run.py" publisher.py \
  --mode manual \
  --title "AI Trends 2026" \
  --content-file "/absolute/path/article.md" \
  --cover "/absolute/path/cover.jpg" \
  --json
```

Use direct text only through `--content-text`. `--content` remains an alias for
`--content-file`; a missing path is an error rather than literal article text.

Markdown supports headings, links, ordered and unordered lists, block quotes,
tables, fenced code, inline code, emphasis, and local inline images. Resolve relative
image paths from the Markdown file. If the body contains images, skip explicit cover
upload. Use `--no-cover` only when the body has no image and no cover is supplied.

For explicitly authorized automatic publishing:

```bash
python3 "$SKILL_DIR/scripts/run.py" publisher.py \
  --mode auto \
  --title "AI Trends 2026" \
  --content-file "/absolute/path/article.md" \
  --headless \
  --json
```

Automatic publishing succeeds only after Toutiao displays a recognized success
indicator. A final-button click without confirmation returns `publish_unconfirmed`.

## Result contract

With `--json`, authentication commands write one JSON result to stdout. Publisher
commands write newline-delimited JSON events; manual mode emits
`awaiting_manual_review` before waiting for the user.

- Exit `0`: authenticated, input valid, manual review completed, or publish confirmed.
- Exit `1`: runtime, browser interaction, draft, upload, or publish failure.
- Exit `2`: invalid input, missing authentication, or clear confirmation required.

Treat stderr as human-readable diagnostics. Do not parse emojis or prose to determine
success.

## Session management

```bash
# Read local state only
python3 "$SKILL_DIR/scripts/run.py" auth_manager.py status --json

# Verify against Toutiao and refresh state
python3 "$SKILL_DIR/scripts/run.py" auth_manager.py validate --json

# Destructive: require explicit user confirmation first
python3 "$SKILL_DIR/scripts/run.py" auth_manager.py clear --yes --json
```

## Environment

Require Python 3.9+, Google Chrome, and local network access. `scripts/run.py`
bootstraps `scripts/setup_environment.py`, verifies the requirements fingerprint,
and executes the target with the Skill-local `.venv` Python. The shared state directory
uses owner-only permissions. Avoid starting concurrent browser operations against the
same persistent Chrome Profile.

Enable `--debug-screenshots` only when troubleshooting. Screenshots are written under
`output/toutiao-publisher-debug/` by default.
