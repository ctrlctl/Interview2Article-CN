---
inclusion: manual
---

# Transcription Workflow Guide / 转录工作流指南

## Supported Input Formats

- Video: MP4, MOV, AVI, MKV, WebM
- Audio: MP3, WAV, M4A, FLAC, OGG
- Subtitle: SRT, VTT, ASS (if user provides existing subtitles)

## Recommended MCP Servers for Transcription

If the user needs transcription capabilities, suggest configuring one of these:

### Option 1: Local Whisper (recommended for privacy)
```json
{
  "mcpServers": {
    "whisper": {
      "command": "uvx",
      "args": ["whisper-mcp-server@latest"],
      "env": {
        "WHISPER_MODEL": "large-v3",
        "WHISPER_LANGUAGE": "zh"
      }
    }
  }
}
```

### Option 2: Cloud-based (faster, requires API key)
The user can configure any speech-to-text API they prefer (Azure, Google, etc.)

## Workflow Decision Tree

```
User provides video/audio
    ├── Transcription MCP available?
    │   ├── Yes → Use it directly
    │   └── No → Ask user to:
    │       ├── Provide SRT/VTT/TXT transcript
    │       ├── Use external tool (e.g., 飞书妙记, 讯飞听见)
    │       └── Configure a Whisper MCP server
    │
User provides transcript
    └── Proceed to Topic Extraction (Step 2)
```

## Error Handling

- If transcription fails, save partial results and ask user to provide missing segments
- If audio quality is poor, flag the entire segment for human review
- If multiple languages are detected, transcribe each language separately
