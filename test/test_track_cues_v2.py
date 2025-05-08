import unittest
import os

from serato_tools.track_cues_v2 import (
    parse,
    dump,
    modify_entries,
    CUE_COLORS,
    TRACK_COLORS,
)


class WidgetTestCase(unittest.TestCase):
    def setUp(self):
        with open(os.path.abspath("test/data/track_cues_v2.bin"), mode="rb") as fp:
            self.data = fp.read()

    def test_parse_and_dump(self):
        entries = list(parse(self.data))
        self.assertEqual(
            [str(e) for e in entries],
            [
                "ColorEntry(field1=b'\\x00', color=b'\\x99\\xff\\x99')",
                "CueEntry(field1=b'\\x00', index=0, position=29, field4=b'\\x00', color=b'\\x88\\x00\\xcc', field6=b'\\x00\\x00', name='')",
                "CueEntry(field1=b'\\x00', index=1, position=12829, field4=b'\\x00', color=b'\\x00\\xcc\\x00', field6=b'\\x00\\x00', name='LYRICS')",
                "CueEntry(field1=b'\\x00', index=2, position=51229, field4=b'\\x00', color=b'\\xcc\\xcc\\x00', field6=b'\\x00\\x00', name='')",
                "CueEntry(field1=b'\\x00', index=3, position=64029, field4=b'\\x00', color=b'\\xcc\\x88\\x00', field6=b'\\x00\\x00', name='')",
                "CueEntry(field1=b'\\x00', index=4, position=89629, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='')",
                "CueEntry(field1=b'\\x00', index=5, position=102429, field4=b'\\x00', color=b'\\xcc\\xcc\\x00', field6=b'\\x00\\x00', name='LYRICS')",
                "CueEntry(field1=b'\\x00', index=6, position=153629, field4=b'\\x00', color=b'\\xcc\\x88\\x00', field6=b'\\x00\\x00', name='')",
                "CueEntry(field1=b'\\x00', index=7, position=204829, field4=b'\\x00', color=b'\\x88\\x00\\xcc', field6=b'\\x00\\x00', name='')",
                "BpmLockEntry(enabled=False)",
            ],
            "parsed entries",
        )
        new_data = dump(entries)
        self.assertEqual(new_data, self.data, "dump")

        entries = modify_entries(
            entries,
            {
                "cues": [
                    {"field": "color", "func": lambda val: CUE_COLORS["red"]},
                    {"field": "name", "func": lambda val: "NEW" if val == "" else None},
                ],
                "color": [
                    {"field": "color", "func": lambda val: TRACK_COLORS["orange"]},
                ],
            },
            print_changes=False,
        )

        assert entries is not None
        self.assertEqual(
            [str(e) for e in entries],
            [
                "ColorEntry(field1=b'\\x00', color=b'\\xff\\xbb\\x99')",
                "CueEntry(field1=b'\\x00', index=0, position=29, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "CueEntry(field1=b'\\x00', index=1, position=12829, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='LYRICS')",
                "CueEntry(field1=b'\\x00', index=2, position=51229, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "CueEntry(field1=b'\\x00', index=3, position=64029, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "CueEntry(field1=b'\\x00', index=4, position=89629, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "CueEntry(field1=b'\\x00', index=5, position=102429, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='LYRICS')",
                "CueEntry(field1=b'\\x00', index=6, position=153629, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "CueEntry(field1=b'\\x00', index=7, position=204829, field4=b'\\x00', color=b'\\xcc\\x00\\x00', field6=b'\\x00\\x00', name='NEW')",
                "BpmLockEntry(enabled=False)",
            ],
            "modified entries",
        )
        new_data = dump(entries)

        with open(
            os.path.abspath("test/data/track_cues_v2_modified.bin"), mode="rb"
        ) as fp:
            expected_modified_data = fp.read()
        self.assertEqual(new_data, expected_modified_data, "modified data dump")
