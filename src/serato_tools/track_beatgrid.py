#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import collections
import io
import struct
import os
import sys
from typing import cast, overload, TypeVar, Unpack

from mutagen._file import FileType
from mutagen.mp3 import HeaderNotFoundError

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.track_tags import SeratoTag
from serato_tools.utils import logger

_T = TypeVar("_T")


class TrackBeatgrid(SeratoTag):
    GEOB_KEY = "Serato BeatGrid"
    VERSION = (0x01, 0x00)

    NonTerminalBeatgridMarker = collections.namedtuple(
        "NonTerminalBeatgridMarker",
        ("position_s", "beats_till_next_marker"),
    )
    TerminalBeatgridMarker = collections.namedtuple(
        "TerminalBeatgridMarker",
        ("position_s", "bpm"),
    )
    Footer = collections.namedtuple("Footer", ("unknown",))

    NonTerminalBeatgridMarkerEnhanced = collections.namedtuple(
        "NonTerminalBeatgridMarkerEnhanced",
        NonTerminalBeatgridMarker._fields + ("bpm",),
    )

    _EntryList = tuple[Unpack[tuple[_T, ...]], TerminalBeatgridMarker, Footer]
    type EntryList = _EntryList[NonTerminalBeatgridMarker]
    type EntryListEnhanced = _EntryList[NonTerminalBeatgridMarkerEnhanced]

    def __init__(self, file_or_data: SeratoTag.FileOrData):
        self.raw_data: bytes | None = None
        super().__init__(file_or_data)

        self.entries: TrackBeatgrid.EntryList | None = None
        self.enhanced_entries: TrackBeatgrid.EntryListEnhanced | None = None

        if self.raw_data is not None:
            self.entries = cast(TrackBeatgrid.EntryList, tuple(self._parse(self.raw_data)))
            self.enhanced_entries = self._enhance_entries(self.entries)

    def __str__(self) -> str:
        if not self.enhanced_entries:
            raise ValueError("no enhanced_entries set")
        nonterminal_markers, terminal_marker, _footer = self._check_and_split(self.enhanced_entries)
        return "\n".join(str(marker) for marker in (*nonterminal_markers, terminal_marker))

    def _parse(self, data: bytes):
        fp = io.BytesIO(data)
        self._check_version(fp.read(self.VERSION_LEN))

        num_markers = struct.unpack(">I", fp.read(4))[0]
        for i in range(num_markers):
            position_s = struct.unpack(">f", fp.read(4))[0]
            data = fp.read(4)
            if i == num_markers - 1:
                bpm = struct.unpack(">f", data)[0]
                yield TrackBeatgrid.TerminalBeatgridMarker(position_s, bpm)
            else:
                beats_till_next_marker = struct.unpack(">I", data)[0]
                yield TrackBeatgrid.NonTerminalBeatgridMarker(position_s, beats_till_next_marker)

        # TODO: What's the meaning of the footer byte?
        yield TrackBeatgrid.Footer(struct.unpack("B", fp.read(1))[0])
        assert fp.read() == b""

    __SplitEntryList = tuple[list[_T], TerminalBeatgridMarker, Footer]

    @overload
    def _check_and_split(self) -> "__SplitEntryList[NonTerminalBeatgridMarker]": ...
    @overload
    def _check_and_split(self, entries: "_EntryList[_T]") -> "__SplitEntryList[_T]": ...
    def _check_and_split(self, entries: "_EntryList[_T] | None" = None):
        if entries is None:
            if not self.entries:
                raise ValueError("no entries set")
            entries = cast("TrackBeatgrid._EntryList[_T]", self.entries)
        nonterminal_markers: list[_T] = []
        terminal_markers: list[TrackBeatgrid.TerminalBeatgridMarker] = []
        footers: list[TrackBeatgrid.Footer] = []

        for entry in entries:
            if isinstance(
                entry, (TrackBeatgrid.NonTerminalBeatgridMarker, TrackBeatgrid.NonTerminalBeatgridMarkerEnhanced)
            ):
                nonterminal_markers.append(cast(_T, entry))
            elif isinstance(entry, TrackBeatgrid.TerminalBeatgridMarker):
                terminal_markers.append(entry)
            elif isinstance(entry, TrackBeatgrid.Footer):
                footers.append(entry)
            else:
                raise TypeError(f"unexpected value type {entry}")

        assert len(terminal_markers) == 1, f"should only be 1 terminal marker, but #: {len(terminal_markers)}"
        assert len(footers) == 1, f"should only be 1 footer, but #: {len(footers)}"
        assert isinstance(entries[-1], TrackBeatgrid.Footer), "last item should be a footer"
        assert isinstance(entries[-2], TrackBeatgrid.TerminalBeatgridMarker), "last item should be a terminal marker"
        return (nonterminal_markers, terminal_markers[0], footers[0])

    def _dump(self):
        entries = self._check_and_split()
        nonterminal_markers, terminal_marker, footer = entries
        markers = (*nonterminal_markers, terminal_marker)

        fp = io.BytesIO()
        # Write version
        fp.write(self._pack_version())

        # Write markers
        fp.write(struct.pack(">I", len(markers)))
        for marker in markers:
            fp.write(struct.pack(">f", marker.position_s))
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

    @staticmethod
    def _enhance_entries(raw_entries: "TrackBeatgrid.EntryList") -> "TrackBeatgrid.EntryListEnhanced":
        *markers, footer = raw_entries
        enhanced: list[TrackBeatgrid.NonTerminalBeatgridMarkerEnhanced | TrackBeatgrid.TerminalBeatgridMarker] = []
        for i, marker in enumerate(markers):
            if isinstance(marker, TrackBeatgrid.NonTerminalBeatgridMarker):
                next_marker = markers[i + 1]
                time_diff = next_marker.position_s - marker.position_s
                bpm = marker.beats_till_next_marker / time_diff * 60
                enhanced.append(
                    TrackBeatgrid.NonTerminalBeatgridMarkerEnhanced(
                        marker.position_s,
                        marker.beats_till_next_marker,
                        bpm,
                    )
                )
            else:
                enhanced.append(marker)
        return cast(TrackBeatgrid.EntryListEnhanced, (*enhanced, footer))

    BeatPoint = collections.namedtuple(
        "BeatInfo",
        ("position_s", "bpm"),
    )

    def get_beats(self) -> list["TrackBeatgrid.BeatPoint"]:
        """Return a list of BeatInfo(position_s, bpm, index) for all beats in the track."""
        if not isinstance(self.tagfile, FileType):
            raise ValueError("no tagfile set, cannot determine track length")
        if not self.enhanced_entries:
            raise ValueError("no enhanced_entries set")

        nonterminal_markers, terminal_marker, _footer = self._check_and_split(self.enhanced_entries)

        beats_with_bpm: list[TrackBeatgrid.BeatPoint] = []

        for i, marker in enumerate(nonterminal_markers):
            next_pos = (
                nonterminal_markers[i + 1].position_s
                if i + 1 < len(nonterminal_markers)
                else terminal_marker.position_s
            )
            interval = (next_pos - marker.position_s) / marker.beats_till_next_marker
            for j in range(marker.beats_till_next_marker):
                pos = marker.position_s + j * interval
                beats_with_bpm.append(TrackBeatgrid.BeatPoint(position_s=pos, bpm=marker.bpm))

        track_length: float = self.tagfile.info.length
        terminal_interval = 60.0 / terminal_marker.bpm
        pos = terminal_marker.position_s
        while pos <= track_length:
            beats_with_bpm.append(TrackBeatgrid.BeatPoint(position_s=pos, bpm=terminal_marker.bpm))
            pos += terminal_interval

        return beats_with_bpm

    def analyze_and_write(self):
        if not self.tagfile:
            raise Exception("No tagfile set")

        from serato_tools.utils.beatgrid_analyze import analyze_beatgrid

        bpm = float(str(self.tagfile["TBPM"]))
        filename = cast(str, self.tagfile.filename)

        logger.info("Analyzing beat grid...")
        analyzed_breatgrid = analyze_beatgrid(filename, bpm_helper=bpm)

        logger.info("Writing tags...")
        raw_entries: TrackBeatgrid.EntryList = (
            *(
                TrackBeatgrid.NonTerminalBeatgridMarker(position_s, 4)
                for position_s in analyzed_breatgrid.downbeats[:-1]
            ),
            TrackBeatgrid.TerminalBeatgridMarker(analyzed_breatgrid.downbeats[-1], bpm=bpm or analyzed_breatgrid.bpm),
            TrackBeatgrid.Footer(0),
        )

        self.entries = raw_entries
        self.enhanced_entries = self._enhance_entries(self.entries)

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
