---
inclusion: manual
---

# Video-to-Article Standards / 视频转文章规范

## Transcription Quality Standards

- Prefer Whisper large-v3 or equivalent for Chinese transcription
- Always output with timestamps for reference
- Segment by speaker if multiple speakers are detected

## Brand Recognition Rules

When identifying brands and products:
- Cross-reference with known brand databases
- Pay attention to Chinese homophones (同音字) that cause misrecognition:
  - 华为 vs 花为, 化为
  - 苹果 vs 平果
  - 小米 vs 小迷
  - 特斯拉 vs 特死拉
  - 比亚迪 vs 比亚地
- For English brand names transcribed in Chinese, try to recover the original English name
- Tech brands: check against common tech product databases

## Polishing Guidelines

### DO:
- Fix obvious typos from speech recognition
- Correct brand/product name spelling
- Add punctuation where clearly needed
- Fix homophone errors when context makes it unambiguous

### DO NOT:
- Rewrite sentences in "better" Chinese
- Remove filler words (嗯, 啊, 那个) unless they severely impact readability
- Change the speaker's word choices
- Add information not present in the original
- Merge or split paragraphs arbitrarily

## Article Structure Template

```
# 大标题（吸引眼球但不标题党）

> 摘要：用2-3句话概括核心内容

---

## 背景介绍 / Background

## 核心内容1 / Key Topic 1

## 核心内容2 / Key Topic 2

## 总结 / Conclusion

---

*品牌与产品：列出所有提及的品牌*
```

## Image Guidelines

- Product images should be official product shots when possible
- Minimum resolution: 800px wide
- Prefer PNG or high-quality JPEG
- Always add alt text for accessibility
- Caption format: `*▲ Brand Name - Product Name*`

## WeChat Specific Notes

- WeChat articles have a max width of ~677px
- Images are auto-compressed by WeChat
- External image links won't work — must be uploaded to WeChat
- Recommended: export markdown to HTML, then paste into WeChat editor
- Use mdnice.com for best markdown-to-WeChat conversion
