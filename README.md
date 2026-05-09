# Interview2Article-CN

将采访视频/音频转化为微信公众号文章和小红书轮播图的自动化工作流。

## 特色功能

- 🎙️ **一键转录** — Whisper 本地转录，自动检测语言，无需 API key
- 🔍 **智能纠错** — 基于领域知识库自动修正品牌名、人名、专有名词
- 🌐 **双语输出** — 英文采访自动生成中英双语对照，中文采访保留原文
- 🖼️ **自动配图** — DuckDuckGo 搜索产品图片，插入文章对应位置
- 📱 **多平台发布** — 一份 Markdown 同时生成微信公众号 HTML 和小红书轮播图
- 📚 **领域可扩展** — 添加 `domain-*.md` 即可适配任何行业的采访内容

## 快速开始

### 克隆项目

```bash
git clone git@github.com:ctrlctl/Interview2Article-CN.git
cd Interview2Article-CN
```

### 依赖安装

```bash
pip install --user openai-whisper yt-dlp ddgs requests pillow markdown premailer pygments pywin32
```

### 使用方式

在 Kiro CLI 中直接说：

- "帮我把这个视频转成公众号文章" + 提供 URL 或文件路径
- "视频转文章"
- "transcribe and format"

Agent 会自动按照 `.kiro/skills/interview-to-article/skill.md` 中定义的 8 步流程执行。

## 工作流概览

```
视频/音频 URL 或文件
    ↓
Step 1: 转录 + 识别语言 (Whisper + yt-dlp)
    ↓
Step 2: 提取主题
    ↓
Step 3: 修正转录文本 (品牌/人名/专有名词，参考 domain knowledge)
    ↓
Step 4: 提取高光内容
    ↓
Step 5: 起草文章 (双语或纯中文，按内容语言决定)
    ↓
Step 6: 插入产品图片 (DuckDuckGo 搜索)
    ↓
Step 7: 审校定稿 → final_article.md
    ↓
Step 8: 多平台输出
    ├── wechat/  → 微信公众号 HTML (粘贴即发)
    └── xhs/     → 小红书轮播图 (上传即发)
```

## 输出目录结构

每个项目生成一个 `YYMMDD_ShortName/` 文件夹：

```
260508_Bastl/
├── final_article.md      ← 最终文章 (Markdown)
├── wechat/article.html   ← 微信公众号 (复制粘贴到编辑器)
├── xhs/01.png ~ N.png    ← 小红书轮播图
├── images/               ← 产品图片
└── drafts/               ← 中间文件 (转录、主题、品牌表等)
```

## 领域知识

`references/domain-synth.md` 包含合成器领域的：
- 品牌正确拼写 vs Whisper 常见误识别
- 产品名中英对照
- 专业术语表
- 人名对照

处理其他领域时，Agent 会自动检索并生成对应的 `domain-*.md` 文件。你也可以手动编写领域知识文件放在 `.kiro/skills/interview-to-article/references/` 目录下，格式参考 `domain-synth.md`。

## 语言处理规则

| 源语言 | 输出格式 |
|--------|---------|
| 英文为主 | 双语 (中文翻译 + 英文原文) |
| 中文为主 | 纯中文，英文术语保留 |
| 中英混合 | 双语 |
