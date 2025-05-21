#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import sys

from mutagen.mp3 import HeaderNotFoundError

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.track_tags import SeratoTag
from serato_tools.utils import logger


class TrackWaveform(SeratoTag):
    GEOB_KEY = "Serato Overview"
    VERSION = (0x01, 0x05)

    def __init__(self, file_or_data: SeratoTag.FileOrData):
        super().__init__(file_or_data)

        if self.raw_data is None:
            raise ValueError("no waveform yet set")

        self.data = self._parse(self.raw_data)

    def _parse(self, data: bytes):
        fp = io.BytesIO(data)
        self._check_version(fp.read(self.VERSION_LEN))

        for x in iter(lambda: fp.read(16), b""):
            assert len(x) == 16
            yield bytearray(x)

    def draw_image(self):
        try:
            from PIL import Image, ImageColor
        except:
            logger.error('must install package "pillow"')
            raise

        img = Image.new("RGB", (240, 16), "black")
        pixels = img.load()

        for i in range(img.size[0]):
            rowdata = next(self.data)
            factor = len([x for x in rowdata if x < 0x80]) / len(rowdata)

            for j, value in enumerate(rowdata):
                # The algorithm to derive the colors from the data has no real mathematical background and was found by experimenting with different values.
                color = "hsl({hue:.2f}, {saturation:d}%, {luminance:.2f}%)".format(
                    hue=(factor * 1.5 * 360) % 360,
                    saturation=40,
                    luminance=(value / 0xFF) * 100,
                )
                pixels[i, j] = ImageColor.getrgb(color)  # pyright: ignore[reportOptionalSubscript]

        return img


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    try:
        tags = TrackWaveform(args.file)
    except HeaderNotFoundError:
        with open(args.file, mode="rb") as fp:
            data = fp.read()
        tags = TrackWaveform(data)

    img = tags.draw_image()
    img.show()
