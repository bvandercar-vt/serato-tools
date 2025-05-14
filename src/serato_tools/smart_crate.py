import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import get_key_from_value, DataTypeError, SERATO_FOLDER


class SmartCrate(CrateBase):
    FOLDER = os.path.join(SERATO_FOLDER, "SmartCrates")

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
        (CrateBase.Fields.SMARTCRATE_MATCH_ALL, [("brut", "0")]),
        (CrateBase.Fields.SMARTCRATE_LIVE_UPDATE, [("brut", "0")]),
        (CrateBase.Fields.SORTING, [(CrateBase.Fields.COLUMN_NAME, "key"), (CrateBase.Fields.REVERSE_ORDER, "\x00")]),
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

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith(".scrate"):
            raise ValueError("file should end with .scrate: " + file)

        super().save(file)

    def __str__(self):
        tracks = self.tracks()
        return f"Smart Crate containing {len(tracks)} tracks (TODO: print rules!): \n" + "\n".join(tracks)

    def print(self):
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                field_lines = []
                for f, f_name, v in value:  # type: ignore
                    if isinstance(v, list):
                        raise TypeError("unexpected type, deeply nested list")
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
            print(f"{field} ({fieldname}): {print_val}")

    @staticmethod
    def list_folder():
        for file in os.listdir(SmartCrate.FOLDER):
            print(os.path.join(SmartCrate.FOLDER, file))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("-f", "--filenames_only", action="store_true")
    parser.add_argument("-d", "--data", action="store_true")
    parser.add_argument("-o", "--output", "--output_file", dest="output_file", default=None)
    args = parser.parse_args()

    if not args.file:
        print(f"must pass a file! files in {SmartCrate.FOLDER}:")
        SmartCrate.list_folder()
        sys.exit()

    crate = SmartCrate(args.file)
    tracks = crate.tracks()
    if args.filenames_only:
        track_names = [os.path.splitext(os.path.basename(track))[0] for track in crate.tracks()]
        print("\n".join(track_names))
    elif args.data:
        crate.print()
    else:
        print(crate)

    if args.output_file:
        crate.save(args.output_file)
