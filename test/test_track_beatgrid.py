# pylint: disable=protected-access
import unittest
import os

from serato_tools.track_beatgrid import TrackBeatgrid


class TestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_beatgrid.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        tags = TrackBeatgrid(self.data)
        self.assertEqual(tags.raw_data, self.data, "raw_data read")
        assert tags.entries is not None
        self.assertEqual(
            tags.entries,
            [
                TrackBeatgrid.TerminalBeatgridMarker(position=0.029895611107349396, bpm=75.0),
                TrackBeatgrid.Footer(unknown=0),
            ],
            "parsed entries",
        )
        tags._dump()
        self.assertEqual(tags.raw_data, self.data, "dump")
