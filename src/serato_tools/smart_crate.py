import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import DataTypeError


class SmartCrate(CrateBase):
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
        ("vrsn", "1.0/Serato ScratchLive Smart Crate"),
        ("rart", [("brut", "0")]),
        ("rlut", [("brut", "0")]),
        ("osrt", [("tvcn", "key"), ("brev", "\x00")]),
        ("ovct", [("tvcn", "song"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "playCount"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "artist"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "bpm"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "key"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "album"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "length"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "comment"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "added"), ("tvcw", "0")]),
    ]

    @staticmethod
    def _get_rule_field_name(value: int) -> str:
        for key, v in SmartCrate.RULE_FIELD.items():
            if v == value:
                return key
        raise ValueError(f"no key for value {value}")

    @staticmethod
    def _get_rule_comparison(value: str) -> str:
        for key, v in SmartCrate.RULE_COMPARISON.items():
            if v == value:
                return key
        raise ValueError(f"no key for value {value}")

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith(".scrate"):
            raise ValueError("file should end with .scrate: " + file)

        super().save(file)

    def __str__(self):
        tracks = self.tracks()
        return f"Crate containing {len(tracks)} tracks (TODO: print rules!): \n" + "\n".join(tracks)

    def print(self):
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                field_lines = []
                for f, f_name, v in value:  # type: ignore
                    if isinstance(v, tuple):
                        raise TypeError("unexpected type")
                    p_val = str(v)
                    if f == "urkt":
                        if not isinstance(v, int):
                            raise DataTypeError(v, int, f)
                        p_val += f" ({self._get_rule_field_name(v)})"
                    elif f == "trft":
                        if not isinstance(v, str):
                            raise DataTypeError(v, str, f)
                        p_val += f" ({self._get_rule_comparison(v)})"
                    field_lines.append(f"[ {f} ({f_name}): {p_val} ]")
                print_val = ", ".join(field_lines)
            else:
                print_val = str(value)
            print(f"{field} ({fieldname}): {print_val}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("-f", "--filenames_only", action="store_true")
    parser.add_argument("-d", "--data", action="store_true")
    parser.add_argument("-o", "--output", "--output_file", dest="output_file", default=None)
    args = parser.parse_args()

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
