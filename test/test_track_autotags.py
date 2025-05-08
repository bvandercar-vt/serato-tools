import unittest
import os
import io

from serato_tools.track_autotags import parse, dump


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_autotags.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        self.bpm, self.autogain, self.gaindb = list(parse(io.BytesIO(self.data)))
        self.assertEqual(self.bpm, 75.0, "parsed bpm")
        self.assertEqual(self.autogain, -5.074, "parsed autogain")
        self.assertEqual(self.gaindb, 0.0, "parsed gaindb")
        new_data = dump(self.bpm, self.autogain, self.gaindb)
        self.assertEqual(new_data, self.data, "dump")
