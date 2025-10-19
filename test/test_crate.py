# pylint: disable=protected-access
import unittest
import os

from src.serato_tools.crate import Crate

with open("test/data/crate.txt", "r", encoding="utf-8") as f:
    base_expected = f.read()


class TestCase(unittest.TestCase):
    def test_format_filepath(self):
        self.assertEqual(
            Crate.get_relative_path("C:\\Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            Crate.get_relative_path("Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            Crate.get_relative_path("C:/Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )
        self.assertEqual(
            Crate.get_relative_path("Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )

    def test_parse_and_modify_and_dump(self):
        file = os.path.abspath("test/data/TestCrate.crate")
        with open(file, mode="rb") as fp:
            file_data = fp.read()

        crate = Crate(file)

        self.maxDiff = None

        self.assertEqual(crate.raw_data, file_data, "raw_data read")
        expected = base_expected

        self.assertEqual(crate.__str__(), expected, "parse")

        crate.add_track("C:\\Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3")
        expected += "\notrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3 ]"
        self.assertEqual(crate.__str__(), expected, "track added")

        for t in [
            "C:\\Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3",
            "Users\\bvand\\Music\\DJ Tracks\\Soulacybin - Zeu.mp3",
            "C:/Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
            "Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
            "/Users/bvand/Music/DJ Tracks/Soulacybin - Zeu.mp3",
        ]:
            crate.add_track(t)
            self.assertEqual(crate.__str__(), expected, "duplicate track not added")

        crate.add_track("C:/Users/bvand/Music/DJ Tracks/Thundercat - Them Changes.mp3")
        expected += "\notrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Thundercat - Them Changes.mp3 ]"
        self.assertEqual(crate.__str__(), expected, "track added")
