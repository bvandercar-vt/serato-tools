# pylint: disable=protected-access
import unittest
import os

from serato_tools.track_autotags import TrackAutotags


class TestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_autotags.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        tags = TrackAutotags(self.data)
        self.assertEqual(tags.raw_data, self.data, "raw_data read")
        self.assertEqual(tags.bpm, 75.0, "parsed bpm")
        self.assertEqual(tags.autogain, -5.074, "parsed autogain")
        self.assertEqual(tags.gaindb, 0.0, "parsed gaindb")
        tags._dump()
        self.assertEqual(tags.raw_data, self.data, "dump")
