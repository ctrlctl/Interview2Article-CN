"""Transcribe already-downloaded audio to SRT using Whisper.

Usage: python transcribe_audio.py <audio> <out.srt> [lang|auto] [model]
"""
import sys
import whisper


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "downloaded_audio.m4a"
    output_srt = sys.argv[2] if len(sys.argv) > 2 else "output.srt"
    language = sys.argv[3] if len(sys.argv) > 3 else "auto"
    model_name = sys.argv[4] if len(sys.argv) > 4 else "small"

    print(f"Loading Whisper model ({model_name})...")
    model = whisper.load_model(model_name)
    print(f"Transcribing: {audio_path} (language={language})")

    kwargs = {"verbose": False}
    if language != "auto":
        kwargs["language"] = language

    result = model.transcribe(str(audio_path), **kwargs)

    print(f"Detected language: {result.get('language')}")

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    print(f"SRT saved: {output_srt}")
    print(f"Total segments: {len(result['segments'])}")


if __name__ == "__main__":
    main()
