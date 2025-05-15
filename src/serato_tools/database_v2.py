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
    DEFAULT_DATABASE_FILE = os.path.join(SERATO_DIR, "database V2")

    DEFAULT_DATA = [
        (SeratoBinFile.Fields.VERSION, "2.0/Serato Scratch LIVE Database"),
    ]

    def __init__(self, file: str = DEFAULT_DATABASE_FILE):
        if not os.path.exists(file):
            raise FileNotFoundError(f"file does not exist: {file}")
        super().__init__(file=file)

    class Track(SeratoBinFile.StructCls):
        def __init__(self, data: "DatabaseV2.Struct"):
            super().__init__(data)

            filepath = self.get_value(DatabaseV2.Fields.FILE_PATH)
            if not isinstance(filepath, str):
                raise DataTypeError(filepath, str, DatabaseV2.Fields.FILE_PATH)
            self.filepath: str = filepath

    class ModifyRule(TypedDict):
        field: SeratoBinFile.Fields
        func: Callable[[str, "DatabaseV2.ValueOrNone"], "DatabaseV2.ValueOrNone"]
        """ (filename: str, prev_value: ValueType | None) -> new_value: ValueType | None """
        files: NotRequired[list[str]]

    class __GeneralModifyRule(ModifyRule):
        field: str  # pyright: ignore[reportIncompatibleVariableOverride]

    def modify(self, rules: list[ModifyRule]):
        DatabaseV2._check_rule_fields(cast(list[DatabaseV2.__GeneralModifyRule], rules))

        for rule in rules:
            if "files" in rule:
                rule["files"] = [DatabaseV2.format_filepath(file).upper() for file in rule["files"]]

        def _maybe_perform_rule(field: str, prev_val: "DatabaseV2.ValueOrNone", track_filename: str):
            rule = next((r for r in rules if field == r["field"]), None)
            if rule is None:
                return None
            if "files" in rule and track_filename.upper() not in rule["files"]:
                return None

            maybe_new_value = rule["func"](track_filename, prev_val)
            if maybe_new_value is None or maybe_new_value == prev_val:
                return None

            if field == DatabaseV2.Fields.FILE_PATH:
                if not isinstance(maybe_new_value, str):
                    raise DataTypeError(maybe_new_value, str, field)
                if not os.path.exists(maybe_new_value):
                    raise FileNotFoundError(f"set track location to {maybe_new_value}, but doesn't exist")
                maybe_new_value = DatabaseV2.format_filepath(maybe_new_value)

            field_name = DatabaseV2.get_field_name(field)
            logger.info(f"Set {field}({field_name})={str(maybe_new_value)} in library for {track_filename}")
            return maybe_new_value

        new_data: DatabaseV2.Struct = []
        for field, value in self.data:
            if field == DatabaseV2.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = DatabaseV2.Track(value)
                for f, v in track.to_struct():
                    maybe_new_value = _maybe_perform_rule(f, v, track.filepath)
                    if maybe_new_value is not None:
                        track.set_value(f, maybe_new_value)
                for rule in rules:
                    if rule["field"] not in track.fields:
                        maybe_new_value = _maybe_perform_rule(rule["field"], None, track.filepath)
                        if maybe_new_value is not None:
                            track.set_value(rule["field"], maybe_new_value)
                value = track.to_struct()
            new_data.append((field, value))

        self.data = new_data
        self._dump()

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

    def remove_duplicates(self):
        new_data: DatabaseV2.Struct = []
        tracks_paths: list[str] = []
        for field, value in self.data:
            if field == DatabaseV2.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = DatabaseV2.Track(value)
                if track.filepath in tracks_paths:
                    # TODO: check if any different aside from date added
                    logger.info(f"removed duplicate: {track.filepath}")
                else:
                    new_data.append((field, value))
                    tracks_paths.append(track.filepath)
            else:
                new_data.append((field, value))
        self.data = new_data
        self._dump()

    def find_missing(self, drive_letter: Optional[str] = None):
        raise NotImplementedError("TODO: debug. This currently ruins the database.")
        if drive_letter is None:  # pylint: disable=unreachable
            drive_letter = os.path.splitdrive(self.filepath)[0]

        track_filepath: str = ""
        missing_checked = False

        def take_input_and_change_db(current_filepath: str):
            while True:
                new_filepath = input("Enter new filepath, or s to skip:")
                new_filepath = new_filepath.strip().strip('"').strip()
                if new_filepath.lower() == "s":
                    return
                if os.path.exists(new_filepath):
                    break
                else:
                    logger.error(f"entered file does not exist: {new_filepath}")

            self.modify(
                [
                    {
                        "field": DatabaseV2.Fields.FILE_PATH,
                        "files": [current_filepath],
                        "func": lambda *args: new_filepath,
                    },
                    {
                        "field": DatabaseV2.Fields.MISSING,
                        "files": [current_filepath],
                        "func": lambda *args: False,
                    },
                ],
            )

        def field_actions(entry: DatabaseV2.EntryFull):
            nonlocal track_filepath
            nonlocal missing_checked
            if entry["field"] == DatabaseV2.Fields.FILE_PATH:
                if not isinstance(entry["value"], str):
                    raise DataTypeError(entry["value"], str, entry["field"])

                value = os.path.join(drive_letter, entry["value"])
                track_filepath = value
                missing_checked = False

                if not os.path.exists(value):
                    logger.error(f"file does not exist: {value}")
                    take_input_and_change_db(current_filepath=entry["value"])
                    missing_checked = True

            elif (not missing_checked) and (entry["field"] == DatabaseV2.Fields.MISSING):
                missing_checked = True
                if entry["value"]:
                    logger.error(f"serato says is missing: {track_filepath}")
                    take_input_and_change_db(current_filepath=track_filepath)

        for entry in list(self.to_entries()):
            if isinstance(entry["value"], list):
                for e in entry["value"]:
                    field_actions(e)
            else:
                field_actions(entry)

        self.save()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=DatabaseV2.DEFAULT_DATABASE_FILE)
    parser.add_argument("--find_missing", action="store_true")
    args = parser.parse_args()

    db = DatabaseV2(args.file)
    if args.find_missing:
        db.find_missing()
    else:
        db.print()
