# Raspberry Pi E‑Ink Word of the Day Display

A small **Raspberry Pi + Waveshare e‑ink display** project that shows a
**daily vocabulary word** in:

-   English
-   Latin American Spanish
-   Brazilian Portuguese

The display updates **once per day** and stays static the rest of the
time --- perfect for low‑power e‑ink displays.

Each word also includes a **QR code linking to the Wiktionary page** so
you can scan it for definitions and usage.

------------------------------------------------------------------------

# Example

Display layout:

    Word of the Day • Jan 03, 2026
    --------------------------------

            resilient

    ES: resiliente
    PT: resiliente

                           [QR]

------------------------------------------------------------------------

# Hardware

Required components:

  Component                            Notes
  ------------------------------------ -------------------
  Raspberry Pi Zero W (or any Pi)      WiFi optional
  Waveshare 2.13" e‑paper display V4   SPI interface
  MicroSD card                         Raspberry Pi OS
  Optional case                        nice desk display

Display resolution:

    250 × 122 pixels

------------------------------------------------------------------------

# Features

-   daily vocabulary word
-   trilingual display
-   QR code to Wiktionary
-   deterministic daily rotation
-   works offline
-   minimal power consumption
-   runs automatically on boot
-   optional scheduled refresh

------------------------------------------------------------------------

# How the Word Rotation Works

The script uses the current date to select a word.

``` python
idx = date.today().toordinal() % len(words)
```

This guarantees:

  Situation                   Result
  --------------------------- -----------
  Pi reboot same day          same word
  script run multiple times   same word
  next day                    new word

No database or state file required.

------------------------------------------------------------------------

# Project Structure

    pi-eink-language-display
    │
    ├── daily_word_trilingual.py
    ├── clear_display.py
    ├── words.json
    ├── systemd
    │   ├── word-display.service
    │   └── word-display.timer
    ├── print
    │   ├── button.STL
    │   ├── shell.STL
    │   └── slide.STL
    └── README.md

------------------------------------------------------------------------

# Words JSON Format

Words are stored locally in `words.json`.

Example:

``` json
[
  {
    "english": { "word": "actually" },
    "spanish": { "word": "en realidad" },
    "portuguese": { "word": "na verdade" }
  },
  {
    "english": { "word": "pretend" },
    "spanish": { "word": "fingir" },
    "portuguese": { "word": "fingir" }
  }
]
```

Characteristics:

-   \~500 words recommended
-   includes many false friends
-   Latin American Spanish
-   Brazilian Portuguese
-   no duplicates

------------------------------------------------------------------------

# Installation

## 1. Enable SPI

    sudo raspi-config

Then:

    Interface Options → SPI → Enable

Reboot if prompted.

------------------------------------------------------------------------

## 2. Create project folder

    mkdir -p ~/Projects/language_learning
    cd ~/Projects/language_learning

------------------------------------------------------------------------

## 3. Install Waveshare library

    git clone https://github.com/waveshare/e-Paper.git

Your library path should be:

    ~/e-Paper/RaspberryPi_JetsonNano/python/lib

------------------------------------------------------------------------

## 4. Create Python virtual environment

    python3 -m venv venv --system-site-packages
    source venv/bin/activate

------------------------------------------------------------------------

## 5. Install dependencies

    pip install pillow qrcode

------------------------------------------------------------------------

## 6. Add project files

    daily_word_trilingual.py
    clear_display.py
    words.json

------------------------------------------------------------------------

# Running the Script

Activate the virtual environment:

    source ~/Projects/language_learning/venv/bin/activate

Run manually:

    python daily_word_trilingual.py

The display updates and then goes to sleep.

------------------------------------------------------------------------

# Clearing the Display

    python clear_display.py

------------------------------------------------------------------------

# Run Automatically at Boot

Create the service:

    sudo nano /etc/systemd/system/word-display.service

    [Unit]
    Description=E-ink Word of the Day
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=oneshot
    User=avanegas
    WorkingDirectory=/home/avanegas/Projects/language_learning
    ExecStart=/home/avanegas/Projects/language_learning/venv/bin/python /home/avanegas/Projects/language_learning/daily_word_trilingual.py

    [Install]
    WantedBy=multi-user.target

Enable it:

    sudo systemctl daemon-reload
    sudo systemctl enable word-display.service
    sudo systemctl start word-display.service

------------------------------------------------------------------------

# Optional Daily Auto Refresh

    sudo nano /etc/systemd/system/word-display.timer

    [Unit]
    Description=Run Word Display Daily

    [Timer]
    OnCalendar=*-*-* 07:00:00
    Persistent=true

    [Install]
    WantedBy=timers.target

Enable:

    sudo systemctl enable --now word-display.timer

------------------------------------------------------------------------
# Case and Battery

## Case

STL files provided by PiSugar: https://github.com/PiSugar/PiSugar

Specific case is pisugar3-slim-pwnagotchi: https://github.com/PiSugar/suit-cases/tree/main/pisugar3-slim-pwnagotchi/print

## Battery 

Battery used is a Pisugar2: https://a.co/d/0btfU6ZJ
------------------------------------------------------------------------

# Troubleshooting

## Display flickers black/white on startup

Normal for e‑ink displays (full refresh to avoid ghosting).

## Check SPI

    ls /dev/spidev*

Should show:

    /dev/spidev0.0
    /dev/spidev0.1

## Check service logs

    journalctl -u word-display.service -n 50

------------------------------------------------------------------------

# Future Improvements

-   spaced repetition
-   difficulty tags
-   themed vocabulary sets
-   example sentences
-   pronunciation QR codes
-   wall mounted frame

------------------------------------------------------------------------

# License

MIT

------------------------------------------------------------------------

# Credits

-   Waveshare e‑paper library
-   Wiktionary
-   PiSugar
