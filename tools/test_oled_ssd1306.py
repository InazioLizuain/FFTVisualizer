#!/usr/bin/env python3
import time


def main() -> int:
    try:
        import board
        import busio
        import adafruit_ssd1306
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        print("Missing dependencies for OLED test.")
        print("Install with: pip3 install adafruit-blinka adafruit-circuitpython-ssd1306 pillow")
        print(f"Import error: {e}")
        return 1

    i2c = busio.I2C(board.SCL, board.SDA)

    width = 128
    height = 64
    oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=0x3C)

    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    oled.fill(0)
    oled.show()

    start = time.time()
    try:
        while time.time() - start < 10:
            t = time.time() - start
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.text((0, 0), "FFTVisualizer", font=font, fill=255)
            draw.text((0, 12), "OLED SSD1306 OK", font=font, fill=255)
            draw.text((0, 24), "Rotate encoder next", font=font, fill=255)

            # simple moving bar
            bar_w = 30
            x = int((width - bar_w) * (0.5 + 0.5 * __import__("math").sin(t * 2.0)))
            draw.rectangle((x, 50, x + bar_w, 62), outline=255, fill=255)

            oled.image(image)
            oled.show()
            time.sleep(0.05)
    finally:
        oled.fill(0)
        oled.show()

    print("OLED test completed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
