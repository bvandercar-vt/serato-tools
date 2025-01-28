#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import struct
import sys

import mutagen
from utils.utils import get_geob, tag_geob

FMT_VERSION = 'BB'

GEOB_KEY = "Serato Autotags"

def readbytes(fp: io.BytesIO | io.BufferedReader):
    for x in iter(lambda: fp.read(1), b''):
        if x == b'\00':
            break
        yield x


def parse(fp: io.BytesIO | io.BufferedReader):
    version = struct.unpack(FMT_VERSION, fp.read(2))
    assert version == (0x01, 0x01)

    for i in range(3):
        data = b''.join(readbytes(fp))
        yield float(data.decode('ascii'))


def dump(bpm: float, autogain: float, gaindb: float):
    data = struct.pack(FMT_VERSION, 0x01, 0x01)
    for value, decimals in ((bpm, 2), (autogain, 3), (gaindb, 3)):
        data += '{:.{}f}'.format(value, decimals).encode('ascii')
        data += b'\x00'
    return data

def main(argv=None):
    import argparse
    import configparser
    import os
    import shutil
    import subprocess
    import tempfile

    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='FILE')
    parser.add_argument('-e', '--edit', action='store_true')
    args = parser.parse_args(argv)

    tagfile = mutagen.File(args.file)
    if tagfile is not None:
        fp = io.BytesIO(get_geob(tagfile, GEOB_KEY))
    else:
        fp = open(args.file, mode='rb')

    with fp:
        bpm, autogain, gaindb = parse(fp)

    if args.edit:
        editor = shutil.which(os.getenv('EDITOR', 'vi'))
        if not editor:
            print('No suitable $EDITOR found.', file=sys.stderr)
            return 1

        with tempfile.NamedTemporaryFile() as f:
            f.write((
                'bpm: {}\n'
                'autogain: {}\n'
                'gaindb: {}\n'
            ).format(bpm, autogain, gaindb).encode('ascii'))
            f.flush()
            status = subprocess.call((editor, f.name))
            f.seek(0)
            output = f.read()

        if status != 0:
            print('Command executation failed with status: {}'.format(status),
                  file=sys.stderr)
            return 1

        cp = configparser.ConfigParser()
        try:
            cp.read_string('[Autotags]\n' + output.decode())
            bpm = cp.getfloat('Autotags', 'bpm')
            autogain = cp.getfloat('Autotags', 'autogain')
            gaindb = cp.getfloat('Autotags', 'gaindb')
        except Exception:
            print('Invalid input, no changes made', file=sys.stderr)
            return 1

        new_data = dump(bpm, autogain, gaindb)
        if tagfile:
            if tagfile is not None:
                tag_geob(tagfile, GEOB_KEY, new_data)
                tagfile.save()
        else:
            with open(args.file, mode='wb') as fp:
                fp.write(new_data)
    else:
        print('BPM: {}'.format(bpm))
        print('Auto Gain: {}'.format(autogain))
        print('Gain dB: {}'.format(gaindb))

    return 0


if __name__ == '__main__':
    sys.exit(main())
