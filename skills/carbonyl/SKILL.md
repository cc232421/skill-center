---
name: carbonyl
description: 终端里的 Chromium 浏览器。当用户说"用终端浏览器打开"、"在 terminal 里浏览网页"、"carbonyl"、"终端渲染网页"、"AI agent 访问网页"、"无界面浏览器"时触发。基于 fathyb/carbonyl (18k+ stars)，无需 GUI 环境即可渲染完整网页。
allowed-tools: Bash, Read
compatibility: "Claude Code ≥1.0"
---

# Carbonyl

终端里的 Chromium 浏览器——把网页渲染成 ANSI 彩色终端界面，无需显示器，支持 WebGL、音视频、60 FPS。

## 安装

> **macOS 关键依赖**：Carbonyl 需要设置 `DYLD_LIBRARY_PATH` 指向二进制所在目录（依赖同目录下的 `.dylib` 文件）。每次调用都要带上，建议加入 shell profile。

将以下内容加入 `~/.zshrc` 或 `~/.bashrc`：
```bash
export DYLD_LIBRARY_PATH="$HOME/.local/bin:$DYLD_LIBRARY_PATH"
```

运行前检测，未安装则自动下载：

```bash
if ! command -v carbonyl &>/dev/null; then
  OS=$(uname -s); ARCH=$(uname -m)
  case "${OS}-${ARCH}" in
    Darwin-arm64)  URL="https://github.com/fathyb/carbonyl/releases/download/v0.0.3/carbonyl.macos-arm64.zip" ;;
    Darwin-x86_64) URL="https://github.com/fathyb/carbonyl/releases/download/v0.0.3/carbonyl.macos-amd64.zip" ;;
    Linux-aarch64) URL="https://github.com/fathyb/carbonyl/releases/download/v0.0.3/carbonyl.linux-arm64.zip" ;;
    Linux-x86_64)  URL="https://github.com/fathyb/carbonyl/releases/download/v0.0.3/carbonyl.linux-amd64.zip" ;;
  esac
  if [ -n "$URL" ]; then
    TMP=$(mktemp -d)
    curl -fSL "$URL" -o "$TMP/c.zip" && unzip -o "$TMP/c.zip" -d "$TMP"
    mkdir -p ~/.local/bin
    cp -r "$TMP"/carbonyl-*/* ~/.local/bin/
    chmod +x ~/.local/bin/carbonyl
    rm -rf "$TMP"
    echo "Carbonyl installed to ~/.local/bin"
  else
    echo "Unsupported platform. Try: npm install --global carbonyl"
  fi
fi
```

## 核心用法

### 交互式浏览

```bash
DYLD_LIBRARY_PATH=~/.local/bin carbonyl https://example.com
```

在终端里渲染完整网页，支持键盘滚动、Tab 切换焦点、Enter 点击链接。按 `Ctrl+C` 退出。

### FPS 控制（省资源）

```bash
DYLD_LIBRARY_PATH=~/.local/bin carbonyl --fps=10 https://youtube.com
```

限制帧率到 10 FPS，降低 CPU 占用，适合内容变化缓慢的页面。

### 缩放

```bash
DYLD_LIBRARY_PATH=~/.local/bin carbonyl --zoom=200 https://example.com
```

放大 200%，方便在高分屏上查看细节。

### 位图渲染模式

```bash
DYLD_LIBRARY_PATH=~/.local/bin carbonyl --bitmap https://example.com
```

把文字渲染为位图模式（替代 ANSI 文字），视觉效果更接近真实浏览器。

### 调试模式

```bash
DYLD_LIBRARY_PATH=~/.local/bin carbonyl --debug https://example.com
```

输出详细日志，用于排查加载问题。

## 快捷包装脚本

将以下内容保存为 `~/.local/bin/cb` 省去每次输入 `DYLD_LIBRARY_PATH`：

```bash
#!/bin/bash
export DYLD_LIBRARY_PATH="$HOME/.local/bin:$DYLD_LIBRARY_PATH"
exec carbonyl "$@"
```
```bash
chmod +x ~/.local/bin/cb
cb https://example.com
```

## 导航操作

Carbonyl 基于 Chromium，支持标准键盘导航：

| 按键 | 操作 |
|------|------|
| `↑↓←→` | 滚动页面 |
| `Tab` / `Shift+Tab` | 切换焦点元素 |
| `Enter` | 点击焦点链接/按钮 |
| `Ctrl+C` | 退出 |

## 与 gstack browse 的关系

Carbonyl 和 `/browse` 互补：

| 场景 | 推荐工具 |
|------|---------|
| 终端内快速查看网页 | **Carbonyl** |
| 无显示器/服务器上浏览 | **Carbonyl** |
| AI agent 提取网页信息 | **Carbonyl**（在真实终端中运行） |
| 鼠标点击、表单交互 | **/browse** |
| 视觉截图、标注 | **/browse** |
| Cookie 导入、登录流程 | **/browse** |
| 网络请求检查 | **/browse** |

## 已知限制

- v0.0.3 无 `--dump-dom`、`--screenshot`、`--width/height` 等高级 CLI 选项（README 描述了未发布的功能）
- 全屏模式不支持
- 交互依赖终端，无法在纯脚本中自动提取内容（需要配合 expect/管道）

## 参考

- GitHub: https://github.com/fathyb/carbonyl
- 版本: v0.0.3（最新 release，2023-02-18）
- Stars: 18,292
- License: MIT
