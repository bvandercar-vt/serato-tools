#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import io
import struct
import os
import sys
from typing import cast

from mutagen.mp3 import HeaderNotFoundError

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.track_tags import SeratoTag
from serato_tools.utils import logger


class TrackBeatgrid(SeratoTag):
    GEOB_KEY = "Serato BeatGrid"
    VERSION = (0x01, 0x00)

    NonTerminalBeatgridMarker = collections.namedtuple(
        "NonTerminalBeatgridMarker",
        ("position", "beats_till_next_marker"),
    )
    TerminalBeatgridMarker = collections.namedtuple(
        "TerminalBeatgridMarker",
        ("position", "bpm"),
    )

    Footer = collections.namedtuple("Footer", ("unknown",))

    type EntryList = list[TerminalBeatgridMarker | NonTerminalBeatgridMarker | Footer]

    def __init__(self, file_or_data: SeratoTag.FileOrData):
        self.raw_data: bytes | None = None
        super().__init__(file_or_data)

        self.entries: TrackBeatgrid.EntryList | None = None

        if self.raw_data is not None:
            self.entries = list(self._parse(self.raw_data))

    def __str__(self) -> str:
        nonterminal_markers, terminal_markers, footer = self._check_and_split()  # pylint: disable=unused-variable
        markers = nonterminal_markers + terminal_markers
        return f"Beatgrid with {len(markers)} markers"

    def _parse(self, data: bytes):
        fp = io.BytesIO(data)
        self._check_version(fp.read(self.VERSION_LEN))

        num_markers = struct.unpack(">I", fp.read(4))[0]
        for i in range(num_markers):
            position = struct.unpack(">f", fp.read(4))[0]
            data = fp.read(4)
            if i == num_markers - 1:
                bpm = struct.unpack(">f", data)[0]
                yield TrackBeatgrid.TerminalBeatgridMarker(position, bpm)
            else:
                beats_till_next_marker = struct.unpack(">I", data)[0]
                yield TrackBeatgrid.NonTerminalBeatgridMarker(position, beats_till_next_marker)

        # TODO: What's the meaning of the footer byte?
        yield TrackBeatgrid.Footer(struct.unpack("B", fp.read(1))[0])
        assert fp.read() == b""

    def _check_and_split(self):
        if not self.entries:
            raise ValueError("no entries set")

        nonterminal_markers: list[TrackBeatgrid.NonTerminalBeatgridMarker] = []
        terminal_markers: list[TrackBeatgrid.TerminalBeatgridMarker] = []
        footers: list[TrackBeatgrid.Footer] = []

        for entry in self.entries:
            if isinstance(entry, TrackBeatgrid.NonTerminalBeatgridMarker):
                nonterminal_markers.append(entry)
            elif isinstance(entry, TrackBeatgrid.TerminalBeatgridMarker):
                terminal_markers.append(entry)
            elif isinstance(entry, TrackBeatgrid.Footer):
                footers.append(entry)
            else:
                raise TypeError(f"unexpected value type {entry}")

        assert len(terminal_markers) == 1, f"should only be 1 terminal marker, but #: {len(terminal_markers)}"
        assert len(footers) == 1, f"should only be 1 footer, but #: {len(footers)}"
        assert isinstance(self.entries[-1], TrackBeatgrid.Footer), "last item should be a footer"
        assert isinstance(
            self.entries[-2], TrackBeatgrid.TerminalBeatgridMarker
        ), "last item should be a terminal marker"
        return nonterminal_markers, terminal_markers, footers[0]

    def _dump(self):
        nonterminal_markers, terminal_markers, footer = self._check_and_split()
        markers = nonterminal_markers + terminal_markers

        fp = io.BytesIO()
        # Write version
        fp.write(self._pack_version())

        # Write markers
        fp.write(struct.pack(">I", len(markers)))
        for marker in markers:
            fp.write(struct.pack(">f", marker.position))
            if isinstance(marker, TrackBeatgrid.TerminalBeatgridMarker):
                fp.write(struct.pack(">f", marker.bpm))
            elif isinstance(marker, TrackBeatgrid.NonTerminalBeatgridMarker):
                fp.write(struct.pack(">I", marker.beats_till_next_marker))
            else:
                raise TypeError(f"Unexpected marker type: {type(marker)}")

        # Write footer
        fp.write(struct.pack("B", footer.unknown))

        # Set to self.raw_data
        fp.seek(0)
        self.raw_data = fp.getvalue()

    def analyze_and_write(self):
        if not self.tagfile:
            raise Exception("No tagfile set")

        from serato_tools.utils.beatgrid_analyze import analyze_beatgrid

        bpm = float(str(self.tagfile["TBPM"]))
        filename = cast(str, self.tagfile.filename)

        logger.info("Analyzing beat grid...")
        analyzed_breatgrid = analyze_beatgrid(filename, bpm_helper=bpm)

        logger.info("Writing tags...")
        entries: TrackBeatgrid.EntryList = [
            TrackBeatgrid.NonTerminalBeatgridMarker(position, 4) for position in analyzed_breatgrid.downbeats[:-1]
        ] + [
            TrackBeatgrid.TerminalBeatgridMarker(analyzed_breatgrid.downbeats[-1], bpm=bpm or analyzed_breatgrid.bpm),
            TrackBeatgrid.Footer(0),
        ]

        self.entries = entries

        self._dump()
        self.save()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("-a", "--analyze", action="store_true", help="Analyze dynamic beatgrid and write to file")
    args = parser.parse_args()

    try:
        tags = TrackBeatgrid(args.file)
    except HeaderNotFoundError:
        with open(args.file, mode="rb") as fp:
            data = fp.read()
        tags = TrackBeatgrid(data)

    if args.analyze and tags.tagfile:
        tags.analyze_and_write()
    else:
        if not tags.entries:
            raise ValueError("no entries")
        for entry in tags.entries:
            print(entry)


def main_analyze():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    tags = TrackBeatgrid(args.file)
    tags.analyze_and_write()


if __name__ == "__main__":
    main()
