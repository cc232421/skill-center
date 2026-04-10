---
name: lightpanda
description: |
  Lightpanda — headless browser for AI agents. Use this when the user wants to browse websites, extract page content, scrape data, or access any URL on a server or machine without Chrome/Chromium installed. Triggers on: "browse website", "open URL", "scrape", "extract page content", "headless browser", "no Chrome browser", "server-side browsing", "访问网页", "抓取网页", "无头浏览器", "lightpanda", "lightpanda browser". This is a self-contained browser binary — no Chrome, Chromium, or GUI required. 9x faster, 16x less memory than Chrome headless. Compatible with Claude Code (MCP), OpenClaw (MCP), and OpenCode (MCP). Use this INSTEAD of Carbonyl when AI agent automation is needed — Carbonyl is for human terminal viewing only; Lightpanda gives structured data.
allowed-tools: Bash, Read
compatibility: "Claude Code ≥1.0, OpenClaw, OpenCode"
---

# Lightpanda — Headless Browser for AI Agents

Self-contained headless browser written in Zig. No Chrome/Chromium needed. 9x faster, 16x less memory than Chrome headless.

**Version:** `1.0.0-nightly` (actively developed)

**Three interfaces:**

| Interface | Best for | Command |
|-----------|----------|---------|
| **MCP Server** | AI agents (Claude Code, OpenClaw, OpenCode) — structured tools | `lightpanda mcp` |
| **CLI Fetch** | Quick text/markdown extraction | `lightpanda fetch --dump <fmt> <url>` |
| **CDP Server** | Playwright / Puppeteer automation | `lightpanda serve --port 9222` |

## Installation

### 1. Check if installed

```bash
if command -v lightpanda &>/dev/null; then
  echo "Lightpanda: $(lightpanda version 2>/dev/null || echo 'installed')"
else
  echo "Lightpanda: NOT FOUND"
fi
```

### 2. Auto-install if missing

```bash
_install_lightpanda() {
  local OS ARCH URL
  OS=$(uname -s)
  ARCH=$(uname -m)

  case "${OS}-${ARCH}" in
    Darwin-arm64)  URL="https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos" ;;
    Darwin-x86_64) URL="https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-macos" ;;
    Linux-arm64)   URL="https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-linux" ;;
    Linux-x86_64)  URL="https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux" ;;
    *)
      echo "Unsupported platform: ${OS}-${ARCH}. Use Docker instead."
      echo "Docker: docker run -d --name lightpanda -p 127.0.0.1:9222:9222 lightpanda/browser:nightly"
      return 1
      ;;
  esac

  mkdir -p ~/.local/bin
  echo "Downloading Lightpanda for ${OS}-${ARCH} (~60MB)..."
  if curl -fSL "$URL" -o ~/.local/bin/lightpanda && chmod +x ~/.local/bin/lightpanda; then
    echo "Lightpanda $(lightpanda version) installed to ~/.local/bin/lightpanda"
  else
    echo "Download failed. Try Docker: docker run -d --name lightpanda -p 127.0.0.1:9222:9222 lightpanda/browser:nightly"
    return 1
  fi
}

if ! command -v lightpanda &>/dev/null; then
  _install_lightpanda
fi
```

Add to `~/.zshrc` or `~/.bashrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Docker fallback (any platform)

```bash
# Start container
docker run -d --name lightpanda -p 127.0.0.1:9222:9222 lightpanda/browser:nightly

# Verify
docker exec lightpanda lightpanda version
```

---

## MCP Server Setup (Recommended)

The MCP server exposes structured tools over stdio. Works with Claude Code, OpenClaw, and OpenCode.

### Claude Code

```bash
claude mcp add lightpanda -- ~/.local/bin/lightpanda mcp
```

Or edit `~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "lightpanda": {
      "command": "~/.local/bin/lightpanda",
      "args": ["mcp"]
    }
  }
}
```

### OpenClaw

```bash
/plugin install lightpanda@lightpanda-io/agent-skill
```

Or add MCP directly:
```bash
/opencode mcp add lightpanda -- ~/.local/bin/lightpanda mcp
```

### Docker MCP

If using Docker, configure the MCP server to route through the container:
```bash
claude mcp add lightpanda -- docker exec lightpanda lightpanda mcp
```

Then restart the agent to load the MCP server.

### MCP Flags

```bash
lightpanda mcp --obey-robots          # Respect robots.txt
lightpanda mcp --log-level info        # Verbose logging
lightpanda mcp --log-format pretty      # Human-readable logs
```

---

## MCP Tools Reference

After the MCP server is running, these tools are available:

### Content Extraction (use these first)

| Tool | Args | Description |
|------|------|-------------|
| `markdown` | `url?`, `waitUntil?` | Get page as markdown — **most useful for AI** |
| `links` | `url?`, `waitUntil?` | Extract all hyperlinks as absolute URLs |
| `semantic_tree` | `url?`, `maxDepth?`, `waitUntil?` | Simplified DOM tree for AI reasoning |
| `structuredData` | `url?`, `waitUntil?` | Extract JSON-LD, OpenGraph, meta tags |
| `evaluate` / `eval` | `script`, `url?` | Execute JavaScript in page context |
| `nodeDetails` | `backendNodeId` | Get details of a specific DOM node |

### Navigation

| Tool | Args | Description |
|------|------|-------------|
| `goto` / `navigate` | `url`, `timeout?`, `waitUntil?` | Navigate to URL, load into memory |
| `waitForSelector` | `selector`, `timeout?` | Wait for CSS selector to appear |

### Interaction

| Tool | Args | Description |
|------|------|-------------|
| `interactiveElements` | `url?`, `waitUntil?` | Extract interactive elements |
| `detectForms` | `url?`, `waitUntil?` | Detect forms with fields, types, required status |
| `click` | `backendNodeId` | Click element, returns URL/title |
| `fill` | `backendNodeId`, `text` | Fill text into input |
| `scroll` | `backendNodeId?`, `x?`, `y?` | Scroll window or element |
| `hover` | `backendNodeId` | Hover over element (menus, tooltips) |
| `press` | `key`, `backendNodeId?` | Press keyboard key (Enter, Tab, Escape, ArrowDown...) |
| `selectOption` | `backendNodeId`, `value` | Select option in `<select>` dropdown |
| `setChecked` | `backendNodeId`, `checked` | Check/uncheck checkbox or radio |

### Element Discovery

| Tool | Args | Description |
|------|------|-------------|
| `findElement` | `role?`, `name?` | Find elements by ARIA role and/or accessible name |

### waitUntil options

`load` | `domcontentloaded` | `networkidle` | `done` (default)

---

## CLI Fetch Reference (Fallback)

Use when MCP is not configured.

```bash
lightpanda fetch --dump <format> [options] <url>

Formats (--dump):
  html              Raw HTML
  markdown          Markdown (AI-friendly)
  semantic_tree     Simplified DOM tree
  semantic_tree_text Plain text semantic tree

Navigation options:
  --wait-until load|domcontentloaded|networkidle|done  Wait strategy (default: done)
  --wait-selector <sel>  Wait for CSS selector
  --wait-script <js>     Wait until JS returns truthy
  --wait-ms <N>          Wait N milliseconds

Content options:
  --strip-mode js,css,ui,full    Strip tags from dump
  --with-frames                   Include iframe content
  --with-base                     Add <base> tag

Robot compliance:
  --obey-robots                   Respect robots.txt

Network options:
  --http-proxy <url>              Use HTTP proxy
  --http-timeout <ms>            Request timeout (default: 10000)
  --http-cache-dir <path>         Enable disk caching

Logging:
  --log-level debug|info|warn|error
  --log-format pretty|logfmt
```

**Examples:**
```bash
# Markdown extraction (most common)
lightpanda fetch --dump markdown --wait-until networkidle https://example.com

# HTML
lightpanda fetch --dump html https://example.com

# Respect robots.txt
lightpanda fetch --dump markdown --obey-robots https://example.com

# Wait for content
lightpanda fetch --dump markdown --wait-selector "#content" https://example.com

# Extract all links
lightpanda fetch --dump links https://example.com
```

---

## CDP Server (Advanced)

For Puppeteer / Playwright integration:

```bash
lightpanda serve --host 127.0.0.1 --port 9222
```

Then connect:
```javascript
const browser = await puppeteer.connect({
  browserWSEndpoint: 'ws://127.0.0.1:9222'
});
const page = await browser.newPage();
await page.goto('https://example.com');
```

---

## Known Limitations

| Issue | Workaround |
|-------|-----------|
| Beta / nightly build — verify critical results | Cross-check with `gstack /browse` |
| No screenshot in MCP mode | Use `gstack /browse` or Playwright via CDP |
| Google blocks Lightpanda | Use DuckDuckGo: `https://duckduckgo.com/?q=query` |
| CORS not implemented | Some cross-origin API calls may fail |
| 1 CDP connection per process | Start multiple processes for parallel browsing |

---

## Platform Support

| OS | Arch | Status |
|----|------|--------|
| macOS / Darwin | arm64 (Apple Silicon) | ✅ Binary available |
| macOS / Darwin | x86_64 | ✅ Binary available |
| Linux | arm64 (aarch64) | ✅ Binary available |
| Linux | x86_64 | ✅ Binary available |
| Windows | any | ⚠️ Use Docker or WSL2 |
