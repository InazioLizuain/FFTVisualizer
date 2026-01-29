#!/usr/bin/env python3
import time


def main() -> int:
    try:
        import board
        import busio
        from adafruit_seesaw.seesaw import Seesaw
        from adafruit_seesaw.rotaryio import IncrementalEncoder
        from adafruit_seesaw.digitalio import DigitalIO
    except Exception as e:
        print("Missing dependencies for encoder test.")
        print("Install with: pip3 install adafruit-blinka adafruit-circuitpython-seesaw")
        print(f"Import error: {e}")
        return 1

    i2c = busio.I2C(board.SCL, board.SDA)
    seesaw = Seesaw(i2c, addr=0x49)

    # Default seesaw pin assignments often used by Adafruit examples.
    # Your config.yaml uses (A=18, B=19, SW=24) which matches many boards.
    a_pin = 18
    b_pin = 19
    sw_pin = 24

    encoder = IncrementalEncoder(seesaw, a_pin, b_pin)
    button = DigitalIO(seesaw, sw_pin)
    button.switch_to_input(pull=True)

    last_pos = encoder.position
    last_btn = button.value

    print("Encoder test running for 30s...")
    print("- Rotate: should print position changes")
    print("- Press: should print button events")

    start = time.time()
    while time.time() - start < 30:
        pos = encoder.position
        if pos != last_pos:
            print(f"pos={pos}")
            last_pos = pos

        btn = button.value  # pull-up => True released
        if btn != last_btn:
            print("button=released" if btn else "button=pressed")
            last_btn = btn

        time.sleep(0.02)

    print("Encoder test completed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
