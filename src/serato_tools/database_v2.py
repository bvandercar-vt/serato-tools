#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from typing import Callable, TypedDict, Optional, NotRequired, cast

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import logger, DataTypeError, SERATO_DIR


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

    class ModifyRule(TypedDict):
        field: SeratoBinFile.Fields
        func: Callable[[str, "DatabaseV2.ValueOrNone"], "DatabaseV2.ValueOrNone"]
        """ (filename: str, prev_value: ValueType | None) -> new_value: ValueType | None """
        files: NotRequired[list[str]]

    class __GeneralModifyRule(ModifyRule):
        field: str  # pyright: ignore[reportIncompatibleVariableOverride]

    def modify(self, rules: list[ModifyRule]):
        SeratoBinFile._check_rule_fields(cast(list[DatabaseV2.__GeneralModifyRule], rules))

        for rule in rules:
            if "files" in rule:
                rule["files"] = [DatabaseV2.get_relative_path(file).upper() for file in rule["files"]]

        def _maybe_perform_rule(field: str, prev_val: "DatabaseV2.ValueOrNone", track_relpath: str):
            rule = next((r for r in rules if field == r["field"]), None)
            if rule is None:
                return None
            if "files" in rule and track_relpath.upper() not in rule["files"]:
                return None

            maybe_new_value = rule["func"](track_relpath, prev_val)
            if maybe_new_value is None or maybe_new_value == prev_val:
                return None

            if field == DatabaseV2.Fields.FILE_PATH:
                if not isinstance(maybe_new_value, str):
                    raise DataTypeError(maybe_new_value, str, field)
                if not os.path.exists(maybe_new_value):
                    raise FileNotFoundError(f"set track location to {maybe_new_value}, but doesn't exist")
                maybe_new_value = DatabaseV2.get_relative_path(maybe_new_value)

            field_name = DatabaseV2.get_field_name(field)
            logger.info(f"Set {field}({field_name})={str(maybe_new_value)} in library for {track_relpath}")
            return maybe_new_value

        def modify_track(track: DatabaseV2.Track) -> DatabaseV2.Track:
            for f, v in track.to_entries():
                maybe_new_value = _maybe_perform_rule(f, v, track.relpath)
                if maybe_new_value is not None:
                    track.set_value(f, maybe_new_value)
            for rule in rules:
                if rule["field"] not in track.fields:
                    maybe_new_value = _maybe_perform_rule(rule["field"], None, track.relpath)
                    if maybe_new_value is not None:
                        track.set_value(rule["field"], maybe_new_value)
            return track

        self.modify_tracks(modify_track)

    def modify_and_save(self, rules: list[ModifyRule], file: Optional[str] = None):
        self.modify(rules)
        self.save(file)

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
