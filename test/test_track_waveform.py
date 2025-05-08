import unittest
import os

from serato_tools.track_waveform import TrackWaveform


class TestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_waveform.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse(self):
        tags = TrackWaveform(self.data)
        self.assertEqual(tags.raw_data, self.data, "raw_data read")
        with open(
            os.path.abspath("test/data/track_waveform_parsed.bin"), mode="rb"
        ) as fp:
            expected_parsed_data = fp.read()
        self.assertEqual(
            b"".join(bytes(x) for x in list(tags.data)),
            expected_parsed_data,
            "parsed data",
        )
