import unittest
import os

from serato_tools.track_cues_v1 import TrackCuesV1


class TestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_cues_v1.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse(self):
        tags = TrackCuesV1(self.data)
        self.assertEqual(tags.raw_data, self.data, "raw_data read")

    @unittest.skip("doesn't work with old data")
    def test_parse_and_dump(self):
        tags = TrackCuesV1(self.data)
        self.assertEqual(tags.raw_data, self.data, "raw_data read")
        tags._dump()
        self.assertEqual(tags.raw_data, self.data, "dump")
