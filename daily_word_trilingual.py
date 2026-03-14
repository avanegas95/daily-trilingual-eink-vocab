#!/usr/bin/env python3
import json
import os
import random
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import qrcode
import smbus
from PIL import Image, ImageDraw, ImageFont

# Waveshare import
# Adjust this if your local library path/module name differs.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from waveshare_epd import epd2in13_V4


# =========================
# Paths / Config
# =========================
BASE_DIR = Path(__file__).resolve().parent
WORDS_FILE = BASE_DIR / "words.json"

DISPLAY_WIDTH = 250
DISPLAY_HEIGHT = 122

PADDING = 8
TOP_STATUS_H = 16
CONTENT_TOP_GAP = 4

HEADER_FONT_SIZE = 12
WORD_MAX_FONT = 34
WORD_MIN_FONT = 16
LANG_SIZE = 16

QR_SIZE = 52
QR_BORDER = 1

BATTERY_X = DISPLAY_WIDTH - 52
BATTERY_Y = 2

PISUGAR_ADDR = 0x32
PISUGAR_REG_BATTERY = 0x02


# =========================
# Fonts
# =========================
def load_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_bold_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# =========================
# Helpers
# =========================
def clamp(value, low, high):
    return max(low, min(high, value))


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_word_font(draw, text, max_width, max_size=WORD_MAX_FONT, min_size=WORD_MIN_FONT):
    for size in range(max_size, min_size - 1, -1):
        font = load_bold_font(size)
        w, _ = text_size(draw, text, font)
        if w <= max_width:
            return font
    return load_bold_font(min_size)


def wrap_text_to_width(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _ = text_size(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


# =========================
# Battery via I2C
# =========================
def read_pisugar_raw():
    bus = smbus.SMBus(1)
    try:
        raw = bus.read_byte_data(PISUGAR_ADDR, PISUGAR_REG_BATTERY)
        return raw
    finally:
        bus.close()


def raw_to_voltage(raw):
    # Estimated mapping for direct I2C fallback.
    # Tune later if needed on your device.
    return 3.0 + (raw * 0.02)


def voltage_to_percent(voltage):
    curve = [
        (4.20, 100),
        (4.15, 95),
        (4.11, 90),
        (4.08, 85),
        (4.02, 80),
        (3.98, 70),
        (3.95, 60),
        (3.91, 50),
        (3.87, 40),
        (3.85, 30),
        (3.82, 20),
        (3.79, 15),
        (3.77, 10),
        (3.73, 5),
        (3.70, 0),
    ]

    if voltage >= curve[0][0]:
        return 100
    if voltage <= curve[-1][0]:
        return 0

    for i in range(len(curve) - 1):
        v1, p1 = curve[i]
        v2, p2 = curve[i + 1]
        if v1 >= voltage >= v2:
            ratio = (voltage - v2) / (v1 - v2)
            return round(p2 + ratio * (p1 - p2))

    return 0


def safe_get_battery_info():
    try:
        raw = read_pisugar_raw()
        voltage = raw_to_voltage(raw)
        percent = clamp(voltage_to_percent(voltage), 0, 100)
        return {
            "raw": raw,
            "voltage": round(voltage, 2),
            "percent": percent,
            "ok": True,
        }
    except Exception as e:
        return {
            "raw": None,
            "voltage": None,
            "percent": None,
            "ok": False,
            "error": str(e),
        }


# =========================
# Words data
# =========================
def load_words():
    if not WORDS_FILE.exists():
        raise FileNotFoundError(f"words.json not found at {WORDS_FILE}")

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("words.json must contain a non-empty list")

    return data


def pick_word(words):
    today_seed = datetime.now().strftime("%Y-%m-%d")
    rng = random.Random(today_seed)
    return rng.choice(words)


def normalize_entry(entry):
    required = ["en", "es", "pt"]
    for key in required:
        if key not in entry:
            raise ValueError(f"Missing key '{key}' in word entry: {entry}")

    wiki_url = entry.get("wiki") or f"https://en.wiktionary.org/wiki/{entry['en']}"
    return {
        "en": str(entry["en"]).strip(),
        "es": str(entry["es"]).strip(),
        "pt": str(entry["pt"]).strip(),
        "wiki": wiki_url.strip(),
    }


# =========================
# Drawing helpers
# =========================
def draw_battery(draw, x, y, percent):
    body_w = 20
    body_h = 10
    tip_w = 2
    tip_h = 4

    # outline
    draw.rectangle((x, y, x + body_w, y + body_h), outline=0, fill=255)
    draw.rectangle(
        (x + body_w + 1, y + (body_h - tip_h) // 2, x + body_w + tip_w, y + (body_h + tip_h) // 2),
        outline=0,
        fill=255,
    )

    fill_margin = 2
    usable_w = body_w - (fill_margin * 2)
    fill_w = round((percent / 100.0) * usable_w)
    if fill_w > 0:
        draw.rectangle(
            (x + fill_margin, y + fill_margin, x + fill_margin + fill_w, y + body_h - fill_margin),
            fill=0,
        )

    label_font = load_font(10)
    draw.text((x + body_w + 6, y - 1), f"{percent}%", font=label_font, fill=0)


def draw_status_bar(draw, battery_info):
    small_font = load_font(HEADER_FONT_SIZE)
    now_txt = datetime.now().strftime("%b %d %I:%M %p").lstrip("0")

    draw.text((PADDING, 1), now_txt, font=small_font, fill=0)

    if battery_info["ok"] and battery_info["percent"] is not None:
        draw_battery(draw, BATTERY_X, BATTERY_Y, battery_info["percent"])
    else:
        draw.text((DISPLAY_WIDTH - 40, 1), "--%", font=small_font, fill=0)

    draw.line((0, TOP_STATUS_H, DISPLAY_WIDTH, TOP_STATUS_H), fill=0, width=1)


# =========================
# Main render
# =========================
def main():
    words = load_words()
    entry = normalize_entry(pick_word(words))

    en_word = entry["en"]
    es_word = entry["es"]
    pt_word = entry["pt"]
    wiki_url = entry["wiki"]

    battery = safe_get_battery_info()

    image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    draw_status_bar(draw, battery)

    safe_w = DISPLAY_WIDTH - (PADDING * 2)
    y = TOP_STATUS_H + CONTENT_TOP_GAP + 2

    # English word
    word_font = fit_word_font(draw, en_word, max_width=safe_w)
    ww, wh = text_size(draw, en_word, word_font)
    x_word = PADDING + max(0, (safe_w - ww) // 2)
    draw.text((x_word, y), en_word, font=word_font, fill=0)
    y += wh + 8

    # ES / PT
    lang_font = load_font(LANG_SIZE)

    es_lines = wrap_text_to_width(draw, f"ES: {es_word}", lang_font, safe_w)
    for line in es_lines:
        draw.text((PADDING, y), line, font=lang_font, fill=0)
        _, lh = text_size(draw, line, lang_font)
        y += lh + 2

    y += 2

    pt_lines = wrap_text_to_width(draw, f"PT: {pt_word}", lang_font, safe_w)
    for line in pt_lines:
        draw.text((PADDING, y), line, font=lang_font, fill=0)
        _, lh = text_size(draw, line, lang_font)
        y += lh + 2

    # QR code (bottom right)
    qr_x = DISPLAY_WIDTH - PADDING - QR_SIZE
    qr_y = DISPLAY_HEIGHT - PADDING - QR_SIZE
    qr = qrcode.QRCode(border=QR_BORDER)
    qr.add_data(wiki_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((QR_SIZE, QR_SIZE))
    image.paste(qr_img, (qr_x, qr_y))

    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.display(epd.getbuffer(image))
    epd.sleep()
    epd2in13_V4.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()
