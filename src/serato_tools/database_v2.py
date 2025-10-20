#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import logger, SERATO_DIR


class DatabaseV2(SeratoBinFile):
    FILENAME = "database V2"
    DEFAULT_DATABASE_FILE = os.path.join(SERATO_DIR, FILENAME)

    DEFAULT_DATA = [
        (SeratoBinFile.Fields.VERSION, "2.0/Serato Scratch LIVE Database"),
    ]

    def __init__(self, file: str = DEFAULT_DATABASE_FILE):
        if not os.path.exists(file):
            raise FileNotFoundError(f"file does not exist: {file}")
        super().__init__(file=file, track_path_key=DatabaseV2.Fields.FILE_PATH)

    def rename_track_file(self, src: str, dest: str):
        """
        This renames the file path, and also changes the path in the database to point to the new filename, so that
        the renamed file is not missing in the library.
        """
        try:
            os.rename(src=src, dst=dest)
            logger.info(f"renamed {src} to {dest}")
        except FileExistsError:
            # can't just do os.path.exists, doesn't pick up case changes for certain filesystems
            logger.error(f"File already exists with change: {src}")
            return
        self.modify_and_save([{"field": DatabaseV2.Fields.FILE_PATH, "files": [src], "func": lambda *args: dest}])

    # TODO: find_missing function!


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=DatabaseV2.DEFAULT_DATABASE_FILE)
    parser.add_argument("--find_missing", action="store_true", help="List files that do not exist")
    args = parser.parse_args()

    db = DatabaseV2(args.file)

    if args.find_missing:
        # TODO: actually look for that missing flag.
        db.find_missing()
    else:
    print(db)
