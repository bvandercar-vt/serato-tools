#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import SERATO_FOLDER, DeeplyNestedStructError


class Crate(CrateBase):
    FOLDER = os.path.join(SERATO_FOLDER, "Subcrates")

    DEFAULT_DATA = [
        (CrateBase.Fields.VERSION, "1.0/Serato ScratchLive Crate"),
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

    def __str__(self):
        tracks = self.tracks()
        return f"Crate containing {len(tracks)} tracks: \n" + "\n".join(tracks)

    def remove_track(self, filepath: str):
        # filepath name must include the containing folder
        found = False
        for i, dat in enumerate(self.data):
            if dat[0] == Crate.Fields.TRACK:
                crate_track_name = Crate._get_track_name(dat[1])
                if crate_track_name == filepath:
                    self.data.pop(i)
                    found = True

        if not found:
            raise ValueError(f"Track not found in crate: {filepath}")

    def add_track(self, filepath: str):
        # filepath name must include the containing folder
        filepath = self.format_filepath(filepath)

        if filepath in self.tracks():
            return

        self.data.append((Crate.Fields.TRACK, [(Crate.Fields.TRACK_PATH, filepath)]))

    def add_tracks_from_folder(self, folder_path: str, replace: bool = False):
        folder_tracks = [self.format_filepath(os.path.join(folder_path, t)) for t in os.listdir(folder_path)]

        if replace:
            for track in self.tracks():
                if track not in folder_tracks:
                    self.remove_track(track)

        for track in folder_tracks:
            self.add_track(track)

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith(".crate"):
            raise ValueError("file should end with .crate: " + file)

        super().save(file)

    def print(self):
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

    @staticmethod
    def list_folder():
        for file in os.listdir(Crate.FOLDER):
            print(os.path.join(Crate.FOLDER, file))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?")
    parser.add_argument("-f", "--filenames_only", action="store_true")
    parser.add_argument("-d", "--data", action="store_true")
    parser.add_argument("-o", "--output", "--output_file", dest="output_file", default=None)
    args = parser.parse_args()

    if not args.file:
        print(f"must pass a file! files in {Crate.FOLDER}:")
        Crate.list_folder()
        sys.exit()

    crate = Crate(args.file)
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
