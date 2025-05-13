# pylint: disable=protected-access
import unittest
import os
import io

from contextlib import redirect_stdout

from serato_tools.crate import Crate


class TestCase(unittest.TestCase):
    def setUp(self):
        self.file = os.path.abspath("test/data/TestCrate.crate")
        with open(self.file, mode="rb") as fp:
            self.data = fp.read()

    def test_format_filepath(self):
        self.assertEqual(
            Crate.format_filepath("C:\\Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            Crate.format_filepath("Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            Crate.format_filepath("C:/Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )
        self.assertEqual(
            Crate.format_filepath("Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )

    def test_parse_and_modify_and_dump(self):
        crate = Crate(self.file)

        self.maxDiff = None

        def get_print_val():
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                crate.print()
            output = captured_output.getvalue()
            return output

        self.assertEqual(crate.raw_data, self.data, "raw_data read")

        expected = """vrsn (Version): '1.0/Serato ScratchLive Crate'
osrt (Sorting): [ tvcn (Column Name): # ], [ brev (Reverse Order): False ]
ovct (Column): [ tvcn (Column Name): song ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): artist ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): bpm ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): key ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): playCount ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): album ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): length ], [ tvcw (Column Width): 0 ]
ovct (Column): [ tvcn (Column Name): comment ], [ tvcw (Column Width): 0 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Tripp St. - Enlighten.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Slaycub - Visceral Planet.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Zeds Dead - In The Beginning.mp3 ]
"""
        self.assertEqual(get_print_val(), expected, "parse")

        crate.add_track("C:\\Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3")
        expected += "otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3 ]\n"
        self.assertEqual(get_print_val(), expected, "track added")

        for t in [
            "C:\\Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3",
            "Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3",
            "C:/Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
            "Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
            "/Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
        ]:
            crate.add_track(t)
            self.assertEqual(get_print_val(), expected, "duplicate track not added")

        crate.add_track("C:/Users/bvand/Music/DJ Tracks/Thundercat - Them Changes.mp3")
        expected += "otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Thundercat - Them Changes.mp3 ]\n"
        self.assertEqual(get_print_val(), expected, "track added")
