"""Extract SRT subtitles from a video URL or local file using yt-dlp + Whisper.

Language detection: if language is not specified (or set to 'auto'), samples
30 seconds from the middle of the audio to detect the dominant language.
This avoids mis-detecting when the intro is in a different language than
the main content (e.g. Chinese host opening an English interview).
"""
import subprocess
import sys
from pathlib import Path


def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def download_audio(url, output="downloaded_audio.m4a"):
    """Download audio from URL using yt-dlp."""
    subprocess.run([
        "yt-dlp", "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "-o", output, url
    ], check=True)
    return output


def detect_language(model, audio_path, sample_offset_ratio=0.4):
    """Detect dominant language by sampling 30s from the middle of the audio.

    Whisper's built-in detector only looks at the first 30 seconds, which fails
    when the intro language differs from the main content. Sampling from the
    middle gives a better read on the dominant language.
    """
    import whisper
    audio = whisper.load_audio(str(audio_path))
    sr = 16000
    total_samples = len(audio)
    offset = int(total_samples * sample_offset_ratio)
    window = 30 * sr
    sample = audio[offset:offset + window]
    sample = whisper.pad_or_trim(sample)
    mel = whisper.log_mel_spectrogram(sample).to(model.device)
    _, probs = model.detect_language(mel)
    lang = max(probs, key=probs.get)
    return lang, probs[lang]


def transcribe_to_srt(audio_path, output_srt="output.srt", language="auto", model_name="small"):
    """Transcribe audio to SRT using Whisper."""
    import whisper

    print(f"Loading Whisper model ({model_name})...")
    model = whisper.load_model(model_name)

    if language == "auto":
        print("Detecting language from mid-audio sample...")
        language, conf = detect_language(model, audio_path)
        print(f"Detected language: {language} (confidence: {conf:.2%})")

    print(f"Transcribing: {audio_path} (language={language})")
    result = model.transcribe(str(audio_path), language=language, verbose=False)

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    print(f"SRT saved: {output_srt}")
    return output_srt


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_srt.py <URL_or_file> [language] [model]")
        print("  language: auto (default), zh, en, ja, etc.")
        print("  model: small (default), medium, large-v3, etc.")
        sys.exit(1)

    source = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "auto"
    model_name = sys.argv[3] if len(sys.argv) > 3 else "small"
    source_path = Path(source)

    # Determine if source is a local file or URL
    if source_path.exists():
        audio_path = str(source_path)
        print(f"Using local file: {audio_path}")
    else:
        print(f"Downloading from: {source}")
        audio_path = download_audio(source)

    srt_file = transcribe_to_srt(audio_path, language=language, model_name=model_name)
    print(f"Done! Output: {srt_file}")


if __name__ == "__main__":
    main()
