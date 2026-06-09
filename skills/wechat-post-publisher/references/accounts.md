# WeChat Post Publisher Preferences & Multi-Account Settings

## Preferences (EXTEND.md)

Check EXTEND.md existence (priority order):

```bash
# macOS, Linux, WSL, Git Bash
test -f .super-publisher/wechat-post-publisher/EXTEND.md && echo "project"
test -f "${XDG_CONFIG_HOME:-$HOME/.config}/super-publisher/wechat-post-publisher/EXTEND.md" && echo "xdg"
test -f "$HOME/.super-publisher/wechat-post-publisher/EXTEND.md" && echo "user"
```

```powershell
# PowerShell (Windows)
if (Test-Path .super-publisher/wechat-post-publisher/EXTEND.md) { "project" }
$xdg = if ($env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME } else { "$HOME/.config" }
if (Test-Path "$xdg/super-publisher/wechat-post-publisher/EXTEND.md") { "xdg" }
if (Test-Path "$HOME/.super-publisher/wechat-post-publisher/EXTEND.md") { "user" }
```

┌────────────────────────────────────────────────────────┬───────────────────┐
│                          Path                          │     Location      │
├────────────────────────────────────────────────────────┼───────────────────┤
│ .super-publisher/wechat-post-publisher/EXTEND.md           │ Project directory │
├────────────────────────────────────────────────────────┼───────────────────┤
│ $HOME/.super-publisher/wechat-post-publisher/EXTEND.md     │ User home         │
└────────────────────────────────────────────────────────┴───────────────────┘

┌───────────┬───────────────────────────────────────────────────────────────────────────┐
│  Result   │                                  Action                                   │
├───────────┼───────────────────────────────────────────────────────────────────────────┤
│ Found     │ Read, parse, apply settings                                               │
├───────────┼───────────────────────────────────────────────────────────────────────────┤
│ Not found │ Run first-time setup ([references/config/first-time-setup.md](references/config/first-time-setup.md)) → Save → Continue │
└───────────┴───────────────────────────────────────────────────────────────────────────┘

**EXTEND.md Supports**: Default theme | Default color | Default publishing method (api/browser) | Default author | Default open-comment switch | Default fans-only-comment switch | Chrome profile path

First-time setup: [references/config/first-time-setup.md](references/config/first-time-setup.md)

**Minimum supported keys** (case-insensitive, accept `1/0` or `true/false`):

| Key | Default | Mapping |
|-----|---------|---------|
| `default_author` | empty | Fallback for `author` when CLI/frontmatter not provided |
| `need_open_comment` | `1` | `articles[].need_open_comment` in `draft/add` request |
| `only_fans_can_comment` | `0` | `articles[].only_fans_can_comment` in `draft/add` request |

**Recommended EXTEND.md example**:

```md
default_theme: default
default_color: blue
default_publish_method: api
default_author: 超级发布
need_open_comment: 1
only_fans_can_comment: 0
chrome_profile_path: /path/to/chrome/profile
```

**Theme options**: default, grace, simple, modern

**Color presets**: blue, green, vermilion, yellow, purple, sky, rose, olive, black, gray, pink, red, orange (or hex value)

**Value priority**:
1. CLI arguments
2. Frontmatter
3. EXTEND.md (account-level → global-level)
4. Skill defaults

---

## Multi-Account Support

EXTEND.md supports managing multiple WeChat Official Accounts. When `accounts:` block is present, each account can have its own credentials, Chrome profile, and default settings.

**Compatibility rules**:

| Condition | Mode | Behavior |
|-----------|------|----------|
| No `accounts` block | Single-account | Current behavior, unchanged |
| `accounts` with 1 entry | Single-account | Auto-select, no prompt |
| `accounts` with 2+ entries | Multi-account | Prompt to select before publishing |
| `accounts` with `default: true` | Multi-account | Pre-select default, user can switch |

**Multi-account EXTEND.md example**:

```md
default_theme: default
default_color: blue

accounts:
  - name: 超级发布团队
    alias: super
    default: true
    default_publish_method: api
    default_author: 超级发布
    need_open_comment: 1
    only_fans_can_comment: 0
    app_id: your_wechat_app_id
    app_secret: your_wechat_app_secret
  - name: 研发工具箱
    alias: dev-tools
    default_publish_method: browser
    default_author: 研发工具箱
    need_open_comment: 1
    only_fans_can_comment: 0
```

**Per-account keys** (can be set per-account or globally as fallback):
`default_publish_method`, `default_author`, `need_open_comment`, `only_fans_can_comment`, `app_id`, `app_secret`, `chrome_profile_path`

**Global-only keys** (always shared across accounts):
`default_theme`, `default_color`

### Account Selection (Step 0.5)

Insert between Step 0 and Step 1 in the Article Posting Workflow:

```
if no accounts block:
    → single-account mode (current behavior)
elif accounts.length == 1:
    → auto-select the only account
elif --account <alias> CLI arg:
    → select matching account
elif one account has default: true:
    → pre-select, show: "Using account: <name> (--account to switch)"
else:
    → prompt user:
      "Multiple WeChat accounts configured:
       1) <name1> (<alias1>)
       2) <name2> (<alias2>)
       Select account [1-N]:"
```

### Credential Resolution (API Method)

For a selected account with alias `{alias}`:

1. `app_id` / `app_secret` inline in EXTEND.md account block
2. Env var `WECHAT_{ALIAS}_APP_ID` / `WECHAT_{ALIAS}_APP_SECRET` (alias uppercased, hyphens → underscores)
3. `.super-publisher/.env` with prefixed key `WECHAT_{ALIAS}_APP_ID`
4. `~/.super-publisher/.env` with prefixed key
5. Fallback to unprefixed `WECHAT_APP_ID` / `WECHAT_APP_SECRET`

**.env multi-account example**:

```bash
# Account: super
WECHAT_SUPER_APP_ID=your_wechat_app_id
WECHAT_SUPER_APP_SECRET=your_wechat_app_secret

# Account: dev-tools
WECHAT_DEV_TOOLS_APP_ID=your_dev_tools_wechat_app_id
WECHAT_DEV_TOOLS_APP_SECRET=your_dev_tools_wechat_app_secret
```

### Chrome Profile (Browser Method)

Each account uses an isolated Chrome profile for independent login sessions:

| Source | Path |
|--------|------|
| Account `chrome_profile_path` in EXTEND.md | Use as-is |
| Auto-generated from alias | `{shared_profile_parent}/wechat-{alias}/` |
| Single-account fallback | Shared default profile (current behavior) |

### CLI `--account` Argument

All publishing scripts accept `--account <alias>`:

```bash
${BUN_X} {baseDir}/scripts/wechat-api.ts <file> --theme default --account dev-tools
${BUN_X} {baseDir}/scripts/wechat-article.ts --markdown <file> --theme default --account super
${BUN_X} {baseDir}/scripts/wechat-browser.ts --markdown <file> --images ./photos/ --account super
```
