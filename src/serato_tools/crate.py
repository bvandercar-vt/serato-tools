#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import sys

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import DeeplyNestedStructError


class Crate(CrateBase):
    EXTENSION = ".crate"
    DIR = "Subcrates"

    DEFAULT_DATA = [
        (CrateBase.Fields.VERSION, "1.0/Serato ScratchLive Crate"),
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

    def __str__(self):
        tracks = self.track_paths()
        return f"Crate containing {len(tracks)} tracks: \n" + "\n".join(tracks)

    def print(self):  # pylint: disable=arguments-differ
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                field_lines = []
                for f, f_name, v in value:
                    if isinstance(v, list):
                        raise DeeplyNestedStructError
                    field_lines.append(f"[ {f} ({f_name}): {v} ]")
                print_val = ", ".join(field_lines)
            else:
                print_val = str(value)
            print(f"{field} ({fieldname}): {print_val}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("-f", "--filenames_only", action="store_true")
    parser.add_argument("-d", "--data", action="store_true")
    parser.add_argument("-o", "--output", "--output_file", dest="output_file", default=None)
    args = parser.parse_args()

    if not args.file:
        print(f"must pass a file! files in {Crate.DIR}:")
        Crate.list_dir()
        sys.exit()

    crate = Crate(args.file)
    tracks = crate.track_paths()
    if args.filenames_only:
        track_names = [os.path.splitext(os.path.basename(track))[0] for track in crate.track_paths()]
        print("\n".join(track_names))
    elif args.data:
        crate.print()
    else:
        print(crate)

    if args.output_file:
        crate.save(args.output_file)
