import unittest
import os
import io
from datetime import datetime

from contextlib import redirect_stdout

from serato_tools.database_v2 import DatabaseV2


class TestCase(unittest.TestCase):
    def setUp(self):
        self.file = os.path.abspath("test/data/database_v2_test.bin")
        with open(self.file, mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_modify_and_dump(self):
        db = DatabaseV2(self.file)
        db.data = list(db.data)

        self.maxDiff = None

        def get_print_val():
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                db.print()
            output = captured_output.getvalue()
            return output

        self.assertEqual(db.raw_data, self.data, "raw_data read")

        with open("test/data/database_v2_test_output.txt", "r", encoding="utf-16") as f:
            expected = f.read()
            self.assertEqual(get_print_val(), expected, "parse")

        original_data = db.data
        original_raw_data = db.raw_data
        db.modify([])
        db.data = list(db.data)
        self.assertEqual(db.data, original_data, "was not modified")
        self.assertEqual(db.raw_data, original_raw_data, "was not modified")
        self.assertEqual(get_print_val(), expected, "was not modified")

        new_time = int(datetime(2025, 1, 1, 9, 15, 0).timestamp())
        db.modify(
            [
                {"field": "uadd", "func": lambda *args: new_time},
                {"field": "tadd", "func": lambda *args: str(new_time)},
                {"field": "tgrp", "func": lambda *args: "NEW_GROUPING"},
            ]
        )
        db.data = list(db.data)
        with open(
            "test/data/database_v2_test_modified_output.txt", "r", encoding="utf-16"
        ) as f:
            self.assertEqual(get_print_val(), f.read(), "was modified correctly")
        with open("test/data/database_v2_test_modified_output.bin", "rb") as f:
            self.assertEqual(db.raw_data, f.read(), "was modified correctly")

        db.modify(
            [
                {
                    "field": "tgen",
                    "func": lambda *args: "NEW_GENRE",
                    "files": [
                        "Users\\bvand\\Music\\DJ Tracks\\Zeds Dead - In The Beginning.mp3",
                        "C:/Users/bvand/Music/DJ Tracks/Tripp St. - Enlighten.mp3",
                    ],
                },
            ]
        )
        db.data = list(db.data)
        with open("test/data/database_v2_test_modified_output_2.txt", "r") as f:
            self.assertEqual(
                get_print_val(), f.read(), "was modified correctly, given files"
            )
        with open("test/data/database_v2_test_modified_output_2.bin", "rb") as f:
            self.assertEqual(
                db.raw_data, f.read(), "was modified correctly, given files"
            )
