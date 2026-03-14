#!/usr/bin/python3
# -*- coding:utf-8 -*-

import sys

WAVESHARE_LIB = "/home/avanegas/e-Paper/RaspberryPi_JetsonNano/python/lib"
sys.path.append(WAVESHARE_LIB)

from waveshare_epd import epd2in13_V4


def main():
    epd = epd2in13_V4.EPD()
    epd.init()
    epd.Clear(0xFF)
    epd.sleep()
    epd2in13_V4.epdconfig.module_exit(cleanup=True)


if __name__ == "__main__":
    main()