#!/usr/bin/env python3
"""Transcribe audio using Whisper (openai-whisper or faster-whisper)."""

import argparse
import sys
from pathlib import Path


def transcribe_openai_whisper(input_path: str, model_name: str) -> str:
    """Transcribe using openai-whisper."""
    import whisper
    print(f"Loading Whisper model: {model_name}...")
    model = whisper.load_model(model_name)
    print("Transcribing...")
    result = model.transcribe(input_path, verbose=False)
    return result["text"]


def transcribe_faster_whisper(input_path: str, model_name: str) -> str:
    """Transcribe using faster-whisper (fallback)."""
    from faster_whisper import WhisperModel
    print(f"Loading faster-whisper model: {model_name}...")
    model = WhisperModel(model_name, compute_type="int8")
    print("Transcribing...")
    segments, _ = model.transcribe(input_path)
    return " ".join(segment.text for segment in segments)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with Whisper")
    parser.add_argument("--input", required=True, help="Path to audio file (WAV recommended)")
    parser.add_argument("--output", required=True, help="Path to save transcript text")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Try openai-whisper first, fall back to faster-whisper
    transcript = None
    try:
        transcript = transcribe_openai_whisper(str(input_path), args.model)
    except ImportError:
        print("openai-whisper not found, trying faster-whisper...")
        try:
            transcript = transcribe_faster_whisper(str(input_path), args.model)
        except ImportError:
            print("Error: Neither openai-whisper nor faster-whisper is installed.")
            print("Install one: pip install openai-whisper  OR  pip install faster-whisper")
            sys.exit(1)
    except Exception as e:
        print(f"openai-whisper failed ({e}), trying faster-whisper...")
        try:
            transcript = transcribe_faster_whisper(str(input_path), args.model)
        except Exception as e2:
            print(f"Error: Both backends failed. openai-whisper: {e}, faster-whisper: {e2}")
            sys.exit(1)

    # Save transcript
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcript.strip())

    word_count = len(transcript.split())
    print(f"\n✅ Transcript saved to: {output_path}")
    print(f"   Words: {word_count}")
    print(f"   Preview: {transcript[:200].strip()}...")


if __name__ == "__main__":
    main()
