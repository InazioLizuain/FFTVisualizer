#!/usr/bin/env python3

def main() -> int:
    try:
        import sounddevice as sd
    except Exception as e:
        print("Missing dependency: sounddevice")
        print("Install with: pip3 install sounddevice")
        print(f"Import error: {e}")
        return 1

    print("sounddevice version:", getattr(sd, "__version__", "?"))
    print("default device (in,out):", sd.default.device)

    devices = sd.query_devices()
    print("\nInput-capable devices:")
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            print(f"  [{i}] {d['name']} (in={d['max_input_channels']}, default_sr={d.get('default_samplerate')})")

    print("\nTip: run this both as user and as root:")
    print("  python3 tools/test_audio_devices.py")
    print("  sudo python3 tools/test_audio_devices.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
