#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import io
import struct
import sys

FMT_VERSION = "BB"

GEOB_KEY = "Serato BeatGrid"

NonTerminalBeatgridMarker = collections.namedtuple(
    "NonTerminalBeatgridMarker",
    ("position", "beats_till_next_marker"),
)
TerminalBeatgridMarker = collections.namedtuple(
    "TerminalBeatgridMarker",
    ("position", "bpm"),
)

Footer = collections.namedtuple("Footer", ("unknown",))


def parse(fp: io.BytesIO | io.BufferedReader):
    version = struct.unpack(FMT_VERSION, fp.read(2))
    assert version == (0x01, 0x00)

    num_markers = struct.unpack(">I", fp.read(4))[0]
    for i in range(num_markers):
        position = struct.unpack(">f", fp.read(4))[0]
        data = fp.read(4)
        if i == num_markers - 1:
            bpm = struct.unpack(">f", data)[0]
            yield TerminalBeatgridMarker(position, bpm)
        else:
            beats_till_next_marker = struct.unpack(">I", data)[0]
            yield NonTerminalBeatgridMarker(position, beats_till_next_marker)

    # TODO: What's the meaning of the footer byte?
    yield Footer(struct.unpack("B", fp.read(1))[0])
    assert fp.read() == b""


if __name__ == "__main__":
    import argparse

    import mutagen._file

    from utils.tags import get_geob

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    tagfile = mutagen._file.File(args.file)
    if tagfile is not None:
        fp = io.BytesIO(get_geob(tagfile, GEOB_KEY))
    else:
        fp = open(args.file, mode="rb")

    with fp:
        for marker in parse(fp):
            print(marker)
