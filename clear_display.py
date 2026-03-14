#!/usr/bin/python3
# -*- coding:utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from waveshare_epd import epd2in13_V4


def main():
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    epd2in13_V4.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()
