#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import struct
import sys
from typing import Callable, Generator, Iterable, TypedDict, Optional, NotRequired, cast

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import logger, DataTypeError, SERATO_FOLDER


class DatabaseV2(SeratoBinFile):
    DEFAULT_DATABASE_FILE = os.path.join(SERATO_FOLDER, "database V2")

    type Value = bytes | str | int | tuple  # TODO: improve the tuple
    type Parsed = tuple[str, Value]

    type ValueOrNone = Value | None

    def __init__(self, filepath: str = DEFAULT_DATABASE_FILE):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"file does not exist: {filepath}")

        self.filepath: str = os.path.abspath(filepath)

        with open(self.filepath, "rb") as fp:
            self.raw_data: bytes = fp.read()
            self.data: Iterable[DatabaseV2.Parsed] = self._parse_item(self.raw_data)

    def __str__(self):
        return str(list(self.to_entries()))

    @staticmethod
    def _parse_item(item_data: bytes) -> Generator[Parsed, None, None]:
        fp = io.BytesIO(item_data)
        for header in iter(lambda: fp.read(8), b""):
            assert len(header) == 8
            field_ascii: bytes
            length: int
            field_ascii, length = struct.unpack(">4sI", header)
            field: str = field_ascii.decode("ascii")
            type_id: str = DatabaseV2._get_type(field)

            data = fp.read(length)
            assert len(data) == length

            value: bytes | str | tuple
            if type_id in ("o", "r"):  #  struct
                value = tuple(DatabaseV2._parse_item(data))
            elif type_id in ("p", "t"):  # text
                # value = (data[1:] + b"\00").decode("utf-16") # from imported code
                value = data.decode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                value = struct.unpack("?", data)[0]
            elif type_id == "s":  # signed int
                value = struct.unpack(">H", data)[0]
            elif type_id == "u":  # unsigned int
                value = struct.unpack(">I", data)[0]
            else:
                raise ValueError(f"unexpected type for field: {field}")

            yield field, value

    @staticmethod
    def _dump_item(item: Iterable["DatabaseV2.Parsed"]):
        fp = io.BytesIO()

        for field, value in item:
            field_bytes = field.encode("ascii")
            assert len(field_bytes) == 4

            type_id: str = DatabaseV2._get_type(field)

            if type_id in ("o", "r"):  #  struct
                if not isinstance(value, tuple):
                    raise DataTypeError(value, tuple, field)
                data = DatabaseV2._dump_item(value)
            elif type_id in ("p", "t"):  # text
                if not isinstance(value, str):
                    raise DataTypeError(value, str, field)
                # if this ever fails, we did used to do this a different way, see old commits.
                data = value.encode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                if not isinstance(value, bool):
                    raise DataTypeError(value, bool, field)
                data = struct.pack("?", value)
            elif type_id == "s":  # signed int
                if not isinstance(value, int):
                    raise DataTypeError(value, int, field)
                data = struct.pack(">H", value)
            elif type_id == "u":  # unsigned int
                if not isinstance(value, int):
                    raise DataTypeError(value, int, field)
                data = struct.pack(">I", value)
            else:
                raise ValueError(f"unexpected type for field: {field}")

            length = len(data)
            header = struct.pack(">4sI", field_bytes, length)
            fp.write(header)
            fp.write(data)

        return fp.getvalue()

    def _dump(self):
        self.raw_data = DatabaseV2._dump_item(list(self.data))

    class ModifyRule(TypedDict):
        field: SeratoBinFile.Fields
        func: Callable[[str, "DatabaseV2.ValueOrNone"], "DatabaseV2.ValueOrNone"]
        """ (filename: str, prev_value: ValueType | None) -> new_value: ValueType | None """
        files: NotRequired[list[str]]

    class __GeneralModifyRule(ModifyRule):
        field: str  # pyright: ignore[reportIncompatibleVariableOverride]

    def modify(self, rules: list[ModifyRule]):
        self.raw_data = DatabaseV2._modify_data_item(list(self.data), rules)
        self.data = self._parse_item(self.raw_data)

    @staticmethod
    def _modify_data_item(item: Iterable[Parsed], rules: list[ModifyRule]):
        DatabaseV2._check_rule_fields(cast(list[DatabaseV2.__GeneralModifyRule], rules))

        for rule in rules:
            rule["field_found"] = False  # pyright: ignore[reportGeneralTypeIssues]
            if "files" in rule:
                rule["files"] = [DatabaseV2.format_filepath(file).upper() for file in rule["files"]]

        fp = io.BytesIO()

        def _dump(field: str, value: "DatabaseV2.Value"):
            nonlocal rules
            field_bytes = field.encode("ascii")
            assert len(field_bytes) == 4

            type_id: str = DatabaseV2._get_type(field)

            if type_id in ("o", "r"):  #  struct
                if not isinstance(value, tuple):
                    raise DataTypeError(value, tuple, field)
                data = DatabaseV2._modify_data_item(value, rules)
            elif type_id in ("p", "t"):  # text
                if not isinstance(value, str):
                    raise DataTypeError(value, str, field)
                # if this ever fails, we did used to do this a different way, see old commits.
                data = value.encode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                if not isinstance(value, bool):
                    raise DataTypeError(value, bool, field)
                data = struct.pack("?", value)
            elif type_id == "s":  # signed int
                if not isinstance(value, int):
                    raise DataTypeError(value, int, field)
                data = struct.pack(">H", value)
            elif type_id == "u":  # unsigned int
                if not isinstance(value, int):
                    raise DataTypeError(value, int, field)
                data = struct.pack(">I", value)
            else:
                raise ValueError(f"unexpected type for field: {field}")

            length = len(data)
            header = struct.pack(">4sI", field_bytes, length)
            fp.write(header)
            fp.write(data)

        def _maybe_perform_rule(rule: DatabaseV2.ModifyRule, field: str, prev_val: "DatabaseV2.ValueOrNone"):
            nonlocal track_filename
            if track_filename == "" or ("files" in rule and track_filename.upper() not in rule["files"]):
                return None

            maybe_new_value = rule["func"](track_filename, prev_val)
            if maybe_new_value is None or maybe_new_value == prev_val:
                return None

            if rule["field"] == DatabaseV2.Fields.FILE_PATH:
                if not isinstance(maybe_new_value, str):
                    raise DataTypeError(maybe_new_value, str, rule["field"])
                if not os.path.exists(maybe_new_value):
                    raise FileNotFoundError(f"set track location to {maybe_new_value}, but doesn't exist")
                maybe_new_value = DatabaseV2.format_filepath(maybe_new_value)

            field_name = DatabaseV2.get_field_name(field)
            logger.info(f"Set {field}({field_name})={str(maybe_new_value)} in library for {track_filename}")
            return maybe_new_value

        track_filename: str = ""
        for field, value in item:
            if field == DatabaseV2.Fields.FILE_PATH:
                if not isinstance(value, str):
                    raise DataTypeError(value, str, DatabaseV2.Fields.FILE_PATH)
                track_filename = value

            rule = next((r for r in rules if field == r["field"]), None)
            if rule:
                rule["field_found"] = True  # pyright: ignore[reportGeneralTypeIssues]
                maybe_new_value = _maybe_perform_rule(rule, field, value)
                if maybe_new_value is not None:
                    value = maybe_new_value

            _dump(field, value)

        for rule in rules:
            if not rule["field_found"]:  # pyright: ignore[reportGeneralTypeIssues]
                field = rule["field"]
                maybe_new_value = _maybe_perform_rule(rule, field, None)
                if maybe_new_value is not None:
                    _dump(field, maybe_new_value)

        return fp.getvalue()

    def modify_and_save(self, rules: list[ModifyRule], file: Optional[str] = None):
        self.modify(rules)
        self.save(file)

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath
        with open(file, "wb") as write_file:
            write_file.write(self.raw_data)

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
        new_data: list[DatabaseV2.Parsed] = []
        tracks_paths: list[str] = []
        for field, value in list(self.data):
            if isinstance(value, tuple):
                if field == DatabaseV2.Fields.TRACK:
                    for f, v in value:
                        if f == DatabaseV2.Fields.FILE_PATH:
                            if not isinstance(v, str):
                                raise DataTypeError(v, str, f)
                            track_path = v
                            if track_path in tracks_paths:
                                # TODO: check if any different aside from date added
                                logger.info(f"removed duplicate: {track_path}")
                            else:
                                new_data.append((field, value))
                                tracks_paths.append(track_path)
                else:
                    new_data.append((field, value))
            else:
                new_data.append((field, value))
        self.data = new_data
        self._dump()

    type EntryFull = tuple[str, str, str | int | bool | list["DatabaseV2.EntryFull"]]

    def to_entries(self) -> Generator[EntryFull, None, None]:
        for field, value in self.data:
            if isinstance(value, tuple):
                try:
                    new_val: list[DatabaseV2.EntryFull] = [(f, DatabaseV2.get_field_name(f), v) for f, v in value]
                except:
                    logger.error(f"error on {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield (field, DatabaseV2.get_field_name(field), value)

    def print(self):
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                print(f"{field} ({fieldname})")
                for f, f_name, v in value:
                    print(f"    {f} ({f_name}): {str(v)}")
            else:
                print(f"{field} ({fieldname}): {str(value)}")

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
