# pylint: disable=protected-access
import unittest
import os

from mutagen.mp3 import MP3


from src.serato_tools.track_cues_v2 import TrackCuesV2
from src.serato_tools.track_cues_v1 import TrackCuesV1
from src.serato_tools.track_waveform import TrackWaveform
from src.serato_tools.track_autotags import TrackAutotags
from src.serato_tools.utils.track_tags import SeratoTrack


class TestCase(unittest.TestCase):
    def test_file_parse(self):
        tagfile = MP3(os.path.abspath("test/data/test_mp3.mp3"))
        TrackCuesV2(tagfile).delete()
        TrackCuesV1(tagfile).delete()
        TrackWaveform(tagfile).delete()
        TrackAutotags(tagfile).delete()

        self.assertIsNone(TrackCuesV2(tagfile)._get_geob())
        self.assertIsNone(TrackCuesV1(tagfile)._get_geob())
        self.assertIsNone(SeratoTrack(tagfile)._get_geob(TrackWaveform.GEOB_KEY))
        self.assertIsNone(TrackAutotags(tagfile)._get_geob())
