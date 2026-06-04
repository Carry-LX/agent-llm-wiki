# OpenCLI —— 让 Agent 通过登录态浏览器操控任意网站

OpenCLI（github.com/jackwener/OpenCLI，22K+ stars）是一个 Node.js CLI 工具，核心能力是把任意网站变成命令行接口，让 AI Agent 通过用户已登录的 Chrome 浏览器完成导航、填表、点击、提取等操作。

它不是又一个 headless browser 方案。它的关键区别在于：**Agent 操控的是你真实登录态的 Chrome**，不需要额外配置 cookie、token 或 API key。Agent 看到的是带完整登录态、偏好设置、缓存的真实浏览器会话。

## 架构

```
AI Agent (Claude Code / Cursor / Codex / Copilot)
    │  Skill 文件 (.claude/skills/ 或 .agents/skills/)
    ▼
opencli CLI (Node.js, npm: @jackwener/opencli)
    ├── Browser: 浏览器操控原语（open/find/click/type/extract/state...）
    ├── Adapters: 100+ 网站的预写适配器，封装为站点子命令
    │    例如: opencli bilibili hot / opencli zhihu search / opencli twitter timeline
    └── Pipeline: 执行管道 (fetch → browser → download → transform)
    │
    ├── Local Daemon (端口 19825, WebSocket)
    ▼
Chrome Extension (Browser Bridge)
    │  通过 Chrome DevTools Protocol 操控浏览器
    ▼
用户 Chrome（已登录各网站，带完整 cookie）
```

## 三层能力

### 1. 内置适配器（即用命令）

覆盖 100+ 网站，按品类：

| 品类 | 示例站点 |
|------|---------|
| 社交 | Twitter/X, Reddit, 微博, Instagram, Facebook, Bluesky |
| 视频 | B站, YouTube, 抖音, TikTok, 小红书 |
| 购物 | 淘宝, 京东, 1688, Amazon, Coupang, 闲鱼 |
| 知识 | 知乎, 豆瓣, Wikipedia, HackerNews, Medium |
| AI | Claude, ChatGPT, Gemini, Grok, DeepSeek, 豆包, 通义千问 |
| 学术 | arXiv, Google Scholar, PubMed, DBLP, CNKI |
| 金融 | 东方财富, 雪球, Binance, CoinGecko |
| 招聘 | LinkedIn, Boss直聘, Indeed, Upwork |
| 其他 | Spotify, Steam, Jira, Confluence, Docker Hub |

每个站点有多个子命令，例如 B站：`hot` / `search` / `history` / `feed` / `ranking` / `download` / `comments` / `dynamic` / `favorite` / `following` / `me` / `subtitle` / `summary` / `video` / `user-videos`。

### 2. Browser 原语（Agent 直接操控）

Agent 通过 `opencli browser <session> <command>` 操作真实浏览器：

| 命令 | 用途 |
|------|------|
| `open <url>` | 打开 URL |
| `state` | 获取页面 DOM 结构（可访问性树格式，非截图） |
| `find` | 按 CSS selector 或语义定位符查找元素 |
| `click <ref>` | 点击元素 |
| `type <ref> <text>` | 在输入框输入文字 |
| `keys <key>` | 发送键盘事件 |
| `fill <ref> <value>` | 填充表单字段 |
| `extract` | 提取页面数据 |
| `get text <selector>` | 获取元素文本 |
| `get url` / `get title` | 获取页面属性 |
| `scroll <direction>` | 滚动页面 |
| `screenshot` | 截图 |
| `tab list/new/select/close` | 标签页管理 |
| `network` | 拦截网络请求获取 API 数据 |

Agent 操作不是基于截图理解页面，而是基于 **DOM 可访问性树快照**——返回结构化 JSON，包含元素角色、文本、属性、可见性、ref 引用。这比视觉方案更精确、更快、token 更省。

### 3. Skill 系统（Agent 集成入口）

OpenCLI 提供 4 个 Skill，安装到 Claude Code/Cursor/Codex 等 Agent 中：

| Skill | 职责 |
|-------|------|
| `opencli-browser` | 临时操控浏览器：导航、填表、点击、提取 |
| `opencli-adapter-author` | 为还没支持的新网站写可复用适配器 |
| `opencli-autofix` | 已有适配器命令坏了，自动诊断修复 |
| `opencli-usage` | 查询 OpenCLI 支持哪些网站和命令 |

## 与常见方案对比

| 方案 | 登录态 | 反爬对抗 | Agent 集成 | 精度 |
|------|--------|---------|-----------|------|
| Playwright/Puppeteer | 需手动配 cookie | 被检测风险高 | 需自写胶水代码 | DOM 直接访问 |
| Browser Use (视觉) | 需截图+注入登录 | 中等 | 有 Agent 接口 | 视觉定位，偶有误差 |
| **OpenCLI** | 复用真实 Chrome | 低（你在正常用浏览器） | Skill 即装即用 | DOM 结构快照 |
| API 调用 | 需申请 key/token | 不适用 | 需自写胶水 | 最高 |

## 实战验证

在 Windows + Claude Code 环境下完成过完整验证：

**简单任务**（百度搜索 → 点击第一个结果）：
```
opencli browser demo open https://www.baidu.com
opencli browser demo find --css "input#kw"     → ref=1
opencli browser demo type 1 "opencli"
opencli browser demo keys Enter
opencli browser demo find --css ".result h3 a"  → ref=129
opencli browser demo click 129
```
→ 成功跳转到腾讯云开发者社区文章页。

**复杂任务**（B站热榜 → 提取排名 → 点击第一个 → 抓取详情）：
```
opencli browser bl-demo open https://www.bilibili.com/v/popular/all
opencli browser bl-demo find --css ".video-card a"        → 前3个 BV号
opencli browser bl-demo open "https://www.bilibili.com/video/BV1K3Gz6pEoo"
opencli browser bl-demo get text "h1"                     → 视频标题
opencli browser bl-demo get text ".video-info-container"  → 播放量/点赞
```
→ 获取到：453万播放、1.3万赞、全站排行榜第1名。

## 工程要点

### 管道 vs 单步

内置适配器（如 `opencli bilibili hot`）内部走的是 **执行管道**：fetch → browser → transform。适配器可以缓存网络请求结果，避免重复的浏览器交互。

Browser 原语（`opencli browser ...`）则是 **单步执行**，每一步都是一次完整的 CDP 调用。

### Session 与 Tab 管理

- `<session>` 是必需参数，用于隔离并行的浏览器工作。
- 同一个 session 内的操作共享同一个 tab（保持 tab lease 存活）。
- `tab new` 创建新 tab 但不切换默认目标；`tab select <targetId>` 才切换。
- 用完建议 `opencli browser <session> close` 释放资源。

### 元素定位方式

优先使用 CSS selector（`--css`），备选语义定位符（`--role`/`--name`/`--label`/`--text`）。`find` 返回的结果中每个元素有 `ref`（数字引用），后续 `click`/`type`/`get` 直接用 ref 操作——这避免了重复查询和 selector 漂移。

### 反爬对抗

OpenCLI 的关键优势：它操控的是**用户的真实 Chrome 实例**，有完整登录态、cookie、浏览器指纹、TLS 指纹。对目标网站来说，这个请求来自于一个正常的 Chrome 用户，而不是一个 headless 自动化工具。

## 局限与风险

1. **依赖 Chrome 运行**：Agent 操作期间 Chrome 必须保持打开，不适合完全无头服务端场景。
2. **DOM 变更风险**：网站改版后 CSS selector 或 DOM 结构变化，适配器可能失效（此时用 `opencli-autofix` 修复）。
3. **登录要求的网站**：虽然能复用登录态，但某些网站（如知乎、京东）的非登录页会重定向到登录页，无账号则无法浏览。
4. **网络限制**：在中国大陆，Google/V2EX/GitHub 等网站可能无法直连。Agent 通过浏览器访问时同样受此限制。
5. **扩展安全**：Browser Bridge 扩展需要授予对 `chrome://extensions` 的开发者权限，安装非官方来源的扩展有一定安全风险。

## 与其他 Agent 工具的结合

OpenCLI 可以与其他 Agent 模式组合使用：

- **Skill 编排**：`opencli-browser` 可以作为 Workflow 中的一个步骤，负责需要登录态的网页交互。
- **工具检索**：可以将 `opencli browser *` 系列命令注册为大模型的工具，按功能打上 search hint。
- **Badcase 修复**：适配器失效时可以用 `opencli-autofix` 自动诊断 → 修代码 → 验证 → 提交 upstream PR 的闭环。
- **上下文压缩**：`state` 和 `find` 返回的结构化 JSON 比原始 HTML 小几个数量级，天然适合 Agent 上下文。
