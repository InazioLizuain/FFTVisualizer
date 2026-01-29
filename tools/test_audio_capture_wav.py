#!/usr/bin/env python3
import argparse
import time
import wave

import numpy as np


def _float_to_int16(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -1.0, 1.0)
    return (x * 32767.0).astype(np.int16)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a short WAV using sounddevice")
    parser.add_argument("--device", default=None, help="Input device index or name (optional)")
    parser.add_argument("--samplerate", type=int, default=44100)
    parser.add_argument("--channels", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--outfile", default="/tmp/test.wav")
    args = parser.parse_args()

    try:
        import sounddevice as sd
    except Exception as e:
        print("Missing dependency: sounddevice")
        print("Install with: pip3 install sounddevice")
        print(f"Import error: {e}")
        return 1

    device = None
    if args.device is not None:
        # accept numeric or string
        device = int(args.device) if str(args.device).isdigit() else str(args.device)

    frames = int(args.seconds * args.samplerate)
    print(f"Recording {args.seconds}s @ {args.samplerate}Hz, ch={args.channels}, device={device!r} -> {args.outfile}")

    try:
        audio = sd.rec(
            frames,
            samplerate=args.samplerate,
            channels=args.channels,
            dtype="float32",
            device=device,
            blocking=True,
        )
    except Exception as e:
        print(f"Record failed: {e}")
        return 2

    # Convert to int16 WAV
    audio_i16 = _float_to_int16(audio)

    with wave.open(args.outfile, "wb") as wf:
        wf.setnchannels(args.channels)
        wf.setsampwidth(2)
        wf.setframerate(args.samplerate)
        wf.writeframes(audio_i16.tobytes())

    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    print(f"Done. peak={peak:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
