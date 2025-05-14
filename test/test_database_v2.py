# pylint: disable=protected-access
import unittest
import os
import io

from contextlib import redirect_stdout

from serato_tools.database_v2 import DatabaseV2


def get_print_val(db: DatabaseV2):
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        db.print()
    output = captured_output.getvalue()
    return output


class TestCase(unittest.TestCase):
    def test_format_filepath(self):
        self.assertEqual(
            DatabaseV2.format_filepath("C:\\Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            DatabaseV2.format_filepath("Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3"),
            "Music/DJ Tracks/Zeds Dead - In The Beginning.mp3",
        )
        self.assertEqual(
            DatabaseV2.format_filepath("C:/Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )
        self.assertEqual(
            DatabaseV2.format_filepath("Music/DJ Tracks/Tripp St. - Enlighten.mp3"),
            "Music/DJ Tracks/Tripp St. - Enlighten.mp3",
        )

    def test_parse_and_dump(self):
        file = os.path.abspath("test/data/database_v2_test.bin")
        with open(file, mode="rb") as fp:
            file_data = fp.read()

        db = DatabaseV2(file)
        db.data = list(db.data)

        self.maxDiff = None
        self.assertEqual(db.raw_data, file_data, "raw_data read")

        with open("test/data/database_v2_test_output.txt", "r", encoding="utf-16") as f:
            expected = f.read()
            self.assertEqual(get_print_val(db), expected, "parse")

        db._dump()
        self.assertEqual(db.raw_data, file_data, "raw_data read")

    def test_parse_and_modify(self):
        file = os.path.abspath("test/data/database_v2_test.bin")
        with open(file, mode="rb") as fp:
            file_data = fp.read()

        db = DatabaseV2(file)
        db.data = list(db.data)

        self.maxDiff = None
        self.assertEqual(db.raw_data, file_data, "raw_data read")

        with open("test/data/database_v2_test_output.txt", "r", encoding="utf-16") as f:
            expected = f.read()
            self.assertEqual(get_print_val(db), expected, "parse")

        original_data = db.data
        original_raw_data = db.raw_data
        db.modify([])
        db.data = list(db.data)
        self.assertEqual(db.data, original_data, "was not modified")
        self.assertEqual(db.raw_data, original_raw_data, "was not modified")
        self.assertEqual(get_print_val(db), expected, "was not modified")

        new_time = int(1735748100)
        db.modify(
            [
                {"field": DatabaseV2.Fields.DATE_ADDED_U, "func": lambda *args: new_time},
                {"field": DatabaseV2.Fields.DATE_ADDED_T, "func": lambda *args: str(new_time)},
                {"field": DatabaseV2.Fields.GROUPING, "func": lambda *args: "NEW_GROUPING"},
            ]
        )
        db.data = list(db.data)
        with open("test/data/database_v2_test_modified_output.txt", "r", encoding="utf-16") as f:
            self.assertEqual(get_print_val(db), f.read(), "was modified correctly")
        with open("test/data/database_v2_test_modified_output.bin", "rb") as f:
            self.assertEqual(db.raw_data, f.read(), "was modified correctly")

        db.modify(
            [
                {
                    "field": DatabaseV2.Fields.GENRE,
                    "func": lambda *args: "NEW_GENRE",
                    "files": [
                        "Users\\bvand\\Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3",
                        "C:/Users/bvand/Music/DJ Tracks/Tripp St. - Enlighten.mp3",
                    ],
                },
            ]
        )
        db.data = list(db.data)
        with open("test/data/database_v2_test_modified_output_2.txt", "r", encoding="utf-8") as f:
            self.assertEqual(get_print_val(db), f.read(), "was modified correctly, given files")
        with open("test/data/database_v2_test_modified_output_2.bin", "rb") as f:
            self.assertEqual(db.raw_data, f.read(), "was modified correctly, given files")
