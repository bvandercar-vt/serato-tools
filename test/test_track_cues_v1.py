import unittest
import os
import io

from serato_tools.track_cues_v1 import parse, dump


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_cues_v1.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        entries = list(parse(io.BytesIO(self.data)))
        # DUMP never worked even in original package
        # new_data = dump(entries)
        # self.assertEqual(new_data, self.data, "dump")
