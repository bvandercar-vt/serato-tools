# pylint: disable=protected-access
import unittest
import os

from src.serato_tools.track_cues_v2 import TrackCuesV2


class TestCase(unittest.TestCase):
    def test_parse_and_dump(self):
        with open(os.path.abspath("test/data/track_cues_v2.bin"), mode="rb") as fp:
            file_data = fp.read()
        tags = TrackCuesV2(file_data)
        self.assertEqual(
            [str(e) for e in tags.entries],
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
        tags._dump()
        self.assertEqual(tags.raw_data, file_data, "dump")

        tags.modify_entries(
            {
                "cues": [
                    {"field": "color", "func": lambda val: TrackCuesV2.CueColors.RED},
                    {"field": "name", "func": lambda val: "NEW" if val == "" else None},
                ],
                "color": [
                    {"field": "color", "func": lambda val: TrackCuesV2.TrackColors.ORANGE},
                ],
            },
        )

        self.assertEqual(
            [str(e) for e in tags.entries],
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
        tags._dump()

        with open(os.path.abspath("test/data/track_cues_v2_modified.bin"), mode="rb") as fp:
            expected_modified_data = fp.read()
        self.assertEqual(tags.raw_data, expected_modified_data, "modified data dump")
