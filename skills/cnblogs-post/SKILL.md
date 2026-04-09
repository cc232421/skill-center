---
name: cnblogs-post
description: 发布博客文章到博客园 (cnblogs.com)。当用户说"发到博客园"、"发布到cnblogs"、"博客园发帖"、"post to cnblogs"时触发。支持单篇文章、设置分类/标签、存草稿。
---

# cnblogs-post

通过 MetaWeblog XML-RPC API 将博客文章发布到博客园。

## 前置条件

### 1. 获取博客别名 (blogApp)

登录博客园 → 管理后台 `https://i.cnblogs.com/` → 你的博客地址中包含别名。

例如博客地址是 `https://www.cnblogs.com/myblog/`，则 `blogApp = myblog`。

### 2. 凭证配置

有两种方式提供用户名和密码（按优先级）：

**方式 A：环境变量（推荐）**
```bash
export CNBLOGS_USERNAME="你的用户名"
export CNBLOGS_PASSWORD="你的密码"
export CNBLOGS_BLOGAPP="你的博客别名"
```

**方式 B：交互式输入**
首次运行时会提示输入，凭证会保存到 `~/.cnblogs-post/credentials`（文件权限 600）。

## 使用方法

### 基础发帖

```bash
python3 scripts/post.py "文章标题" "文章HTML内容"
```

### 指定分类和标签

```bash
python3 scripts/post.py "文章标题" "文章HTML内容" \
  --category "技术" \
  --tags "Python,API,教程"
```

### 存为草稿（不公开发布）

```bash
python3 scripts/post.py "文章标题" "文章HTML内容" --draft
```

### 完整参数示例

```bash
python3 scripts/post.py \
  --title "用 Claude API 自动化博客发布" \
  --content "<h2>前言</h2><p>本文介绍...</p>" \
  --category "技术" \
  --tags "Claude,API,自动化" \
  --draft
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--title` | 文章标题 |
| `--content` | 文章正文（HTML 格式） |
| `--category` | 主分类名称（如"技术"） |
| `--tags` | 标签，逗号分隔（如"Python,API"） |
| `--draft` | 存为草稿，不公开发布 |
| `--blogapp` | 覆盖默认博客别名 |
| `--username` | 覆盖默认用户名 |
| `--password` | 覆盖默认密码 |

## 输出格式

成功：
```json
{"ok":true,"post_id":"1234567","url":"https://www.cnblogs.com/你的别名/p/1234567.html","title":"文章标题"}
```

失败：
```json
{"ok":false,"error":"错误描述"}
```

## 文章内容格式

MetaWeblog API 要求内容为 HTML。建议：

- 使用标准 HTML 标签（h1-h6, p, pre, code, blockquote 等）
- 代码高亮可用 `<pre><code class="language-python">...</code></pre>`
- 图片需先上传到图床，插入 `<img src="图床URL">`
- 支持 Markdown 需自行转换为 HTML

## 提示

- 内容是 HTML，不是纯文本
- 标签需先在博客园后台创建，或留空
- 草稿可在管理后台 `https://i.cnblogs.com/` 发布
- 连续发帖建议每次间隔 10 秒以上，避免触发频率限制
