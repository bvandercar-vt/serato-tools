#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import io
import struct
import sys

import mutagen
from utils.utils import get_geob

FMT_VERSION = 'BB'

GEOB_KEY = "Serato BeatGrid"

NonTerminalBeatgridMarker = collections.namedtuple(
    'NonTerminalBeatgridMarker', (
        'position',
        'beats_till_next_marker',
    )
)
TerminalBeatgridMarker = collections.namedtuple('TerminalBeatgridMarker', (
    'position',
    'bpm',
))

Footer = collections.namedtuple('Footer', (
    'unknown',
))


def parse(fp: io.BytesIO | io.BufferedReader):
    version = struct.unpack(FMT_VERSION, fp.read(2))
    assert version == (0x01, 0x00)

    num_markers = struct.unpack('>I', fp.read(4))[0]
    for i in range(num_markers):
        position = struct.unpack('>f', fp.read(4))[0]
        data = fp.read(4)
        if i == num_markers - 1:
            bpm = struct.unpack('>f', data)[0]
            yield TerminalBeatgridMarker(position, bpm)
        else:
            beats_till_next_marker = struct.unpack('>I', data)[0]
            yield NonTerminalBeatgridMarker(position, beats_till_next_marker)

    # TODO: What's the meaning of the footer byte?
    yield Footer(struct.unpack('B', fp.read(1))[0])
    assert fp.read() == b''


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='FILE')
    args = parser.parse_args(argv)

    tagfile = mutagen.File(args.file)
    if tagfile is not None:
        fp = io.BytesIO(get_geob(tagfile, GEOB_KEY))
    else:
        fp = open(args.file, mode='rb')

    with fp:
        for marker in parse(fp):
            print(marker)

    return 0


if __name__ == '__main__':
    sys.exit(main())
