import unittest
import os
import io

from serato_tools.track_beatgrid import parse, dump, TerminalBeatgridMarker, Footer


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_beatgrid.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        entries = list(parse(io.BytesIO(self.data)))
        self.assertEqual(
            entries,
            [
                TerminalBeatgridMarker(position=0.029895611107349396, bpm=75.0),
                Footer(unknown=0),
            ],
            "parsed entries",
        )
        fp_dump = io.BytesIO()
        dump(entries, fp_dump)
        self.assertEqual(fp_dump.getvalue(), self.data, "dump")
