import unittest
import os
import io

from serato_tools.track_waveform import parse


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_waveform.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse(self):
        with open(
            os.path.abspath("test/data/track_waveform_parsed.bin"), mode="rb"
        ) as fp:
            expected_parsed_data = fp.read()
        parsed_data = list(parse(io.BytesIO(self.data)))
        self.assertEqual(
            b"".join(bytes(x) for x in parsed_data),
            expected_parsed_data,
            "parsed data",
        )
