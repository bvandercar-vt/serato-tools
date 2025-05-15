import os
import sys

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import get_key_from_value, DataTypeError, DeeplyNestedStructError


class SmartCrate(CrateBase):
    EXTENSION = ".scrate"
    DIR = "SmartCrates"

    RULE_FIELD = {
        "added": 25,
        "album": 8,
        "artist": 7,
        "bpm": 15,
        "comment": 17,
        "composer": 22,
        "filename": 4,
        "genre": 9,
        "grouping": 19,
        "key": 51,
        "label": 21,
        "plays": 79,
        "remixer": 20,
        "song": 6,
        "year": 23,
    }

    RULE_COMPARISON = {
        "STR_CONTAINS": "cond_con_str",
        "STR_DOES_NOT_CONTAIN": "cond_dnc_str",
        "STR_IS": "cond_is_str",
        "STR_IS_NOT": "cond_isn_str",
        "STR_DATE_BEFORE": "cond_bef_str",
        "STR_DATE_AFTER": "cond_aft_str",
        "TIME_IS_BEFORE": "cond_bef_time",
        "TIME_IS_AFTER": "cond_aft_time",
        "INT_IS_GE": "cond_greq_uint",
        "INT_IS_LE": "cond_lseq_uint",
    }

    DEFAULT_DATA = [
        (CrateBase.Fields.VERSION, "1.0/Serato ScratchLive Smart Crate"),
        (CrateBase.Fields.SMARTCRATE_MATCH_ALL, [("brut", False)]),
        (CrateBase.Fields.SMARTCRATE_LIVE_UPDATE, [("brut", False)]),
        (CrateBase.Fields.SORTING, [(CrateBase.Fields.COLUMN_NAME, "key"), (CrateBase.Fields.REVERSE_ORDER, False)]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "song"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "playCount"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "artist"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "bpm"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "key"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "album"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "length"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "comment"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "added"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
    ]

    @staticmethod
    def _get_rule_field_name(value: int) -> str:
        return get_key_from_value(value, SmartCrate.RULE_FIELD)

    @staticmethod
    def _get_rule_comparison(value: str) -> str:
        return get_key_from_value(value, SmartCrate.RULE_COMPARISON)

    def __str__(self):
        lines: list[str] = []
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                field_lines = []
                for f, f_name, v in value:
                    if isinstance(v, list):
                        raise DeeplyNestedStructError
                    p_val = str(v)
                    if f == CrateBase.Fields.RULE_FIELD:
                        if not isinstance(v, int):
                            raise DataTypeError(v, int, f)
                        p_val += f" ({self._get_rule_field_name(v)})"
                    elif f == CrateBase.Fields.RULE_COMPARISON:
                        if not isinstance(v, str):
                            raise DataTypeError(v, str, f)
                        p_val += f" ({self._get_rule_comparison(v)})"
                    field_lines.append(f"[ {f} ({f_name}): {p_val} ]")
                print_val = ", ".join(field_lines)
            else:
                print_val = str(value)
            lines.append(f"{field} ({fieldname}): {print_val}")

        return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("-l", "--list_tracks", action="store_true", help="Only list tracks")
    parser.add_argument("-f", "--filenames_only", action="store_true", help="Only list track filenames")
    parser.add_argument(
        "-o", "--output", "--output_file", dest="output_file", default=None, help="Output file to save the crate to"
    )
    args = parser.parse_args()

    if not args.file:
        print(f"must pass a file! files in {SmartCrate.DIR}:")
        SmartCrate.list_dir()
        sys.exit()

    crate = SmartCrate(args.file)
    if args.list_tracks:
        tracks = crate.get_track_paths()
        if args.filenames_only:
            tracks = [os.path.splitext(os.path.basename(t))[0] for t in tracks]
        print("\n".join(tracks))
    else:
        print(crate)

    if args.output_file:
        crate.save(args.output_file)
