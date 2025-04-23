#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import struct
import sys
from typing import (Any, Callable, Generator, Iterable, NotRequired, Tuple,
                    TypedDict, cast)

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils import DataTypeError


class DbEntry(TypedDict):
    field: str
    field_name: str
    value: str | int | bool | list["DbEntry"]
    size_bytes: int


ValueType = bytes | str | int | tuple  # TODO: improve the tuple
ParsedType = Tuple[str, int, ValueType, bytes]


class DatabaseV2(object):
    FIELDNAMES = {
        # Database
        "vrsn": "Version",
        "otrk": "Track",
        "ttyp": "File Type",
        "pfil": "File Path",
        "tsng": "Song Title",
        "tart": "Artist",
        "talb": "Album",
        "tgen": "Genre",
        "tlen": "Length",
        "tbit": "Bitrate",
        "tsmp": "Sample Rate",
        "tsiz": "Size",
        "tbpm": "BPM",
        "tkey": "Key",
        "tart": "Artist",
        "utme": "File Time",
        "tgrp": "Grouping",
        "tlbl": "Publisher",
        "tcmp": "Composer",
        "ttyr": "Year",
        # Serato stuff
        "tadd": "Date added",
        "uadd": "Date added",
        "bbgl": "Beatgrid Locked",
        "bcrt": "Corrupt",
        "bmis": "Missing",
        # Crates
        "osrt": "Sorting",
        "brev": "Reverse Order",
        "ovct": "Column Title",
        "tvcn": "Column Name",
        "tvcw": "Column Width",
        "ptrk": "Track Path",
    }
    DEFAULT_DATABASE_FILE = os.path.join(os.path.expanduser("~"), "Music\\_Serato_\\database V2")  # type: ignore

    def __init__(self, filepath: str = DEFAULT_DATABASE_FILE):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"file does not exist: {filepath}")

        self.filepath: str = os.path.abspath(filepath)

        self.data: Iterable[ParsedType] = self._parse(self.filepath)

    def __str__(self):
        return str(list(self.to_objects()))

    @staticmethod
    def _get_field_name(field: str):
        return DatabaseV2.FIELDNAMES.get(field, "Unknown Field")

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field contains text but does not start with the "t" type_id
        return "t" if field == "vrsn" else field[0]

    def _parse(
        self, fp: io.BytesIO | io.BufferedReader | str | None
    ) -> Generator[ParsedType]:
        if fp is None:
            fp = self.filepath
        if isinstance(fp, str):
            fp = open(fp, "rb")

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
                value = tuple(self._parse(io.BytesIO(data)))
            elif type_id in ("p", "t"):  # text
                value = (data[1:] + b"\00").decode("utf-16")
            elif type_id == "b":  # bytes
                value = struct.unpack("?", data)[0]
            elif type_id == "s":  # signed
                value = struct.unpack(">H", data)[0]
            elif type_id == "u":  # unsigned
                value = struct.unpack(">I", data)[0]
            else:
                value = data

            yield field, length, value, data

    class ModifyRule(TypedDict):
        field: str
        func: Callable[[str, Any], Any]
        files: NotRequired[list[str]]

    @staticmethod
    def _modify_data(
        fp: io.BytesIO | io.BufferedWriter,
        item: Iterable[ParsedType],
        rules: list[ModifyRule] = [],
        print_changes: bool = True,
    ):
        all_field_names = [rule["field"] for rule in rules]
        assert len(rules) == len(
            list(set(all_field_names))
        ), f"must only have 1 function per field. fields passed: {str(all_field_names)}"

        for rule in rules:
            rule["field_found"] = False  # type: ignore
            if "files" in rule:
                rule["files"] = [
                    os.path.normpath(os.path.splitdrive(file)[1]).lstrip("\\").upper()
                    for file in rule["files"]
                ]

        def _dump(field: str, value: ValueType, data: bytes):
            nonlocal rules, print_changes
            field_bytes = field.encode("ascii")
            assert len(field_bytes) == 4

            type_id: str = DatabaseV2._get_type(field)

            if type_id in ("o", "r"):  #  struct
                if not isinstance(value, tuple):
                    raise DataTypeError(value, tuple, field)
                nested_buffer = io.BytesIO()
                DatabaseV2._modify_data(nested_buffer, value, rules, print_changes)
                data = nested_buffer.getvalue()
            elif type_id in ("p", "t"):  # text
                if not isinstance(value, str):
                    raise DataTypeError(value, str, field)
                new_data = value.encode("utf-16")[2:]
                assert new_data[-1:] == b"\x00"
                data = data[:1] + new_data[:-1]
            else:
                if not isinstance(value, (bytes, int)):
                    raise DataTypeError(value, (bytes, int), field)
                if type_id == "s":  # signed
                    data = struct.pack(">H", value)
                elif type_id == "b":  # bytes
                    data = struct.pack("?", value)
                elif type_id == "u":  # unsigned
                    data = struct.pack(">I", value)

            length = len(data)
            header = struct.pack(">4sI", field_bytes, length)
            fp.write(header)
            fp.write(data)

        def _maybe_perform_rule(rule: DatabaseV2.ModifyRule, field: str, prev_val: Any):
            nonlocal track_filename
            if track_filename == "" or (
                "files" in rule and track_filename.upper() not in rule["files"]
            ):
                return None

            maybe_new_value = rule["func"](track_filename, prev_val)
            if maybe_new_value is None or maybe_new_value == prev_val:
                return None

            if print_changes:
                print(
                    f"Set {field}({DatabaseV2._get_field_name(field)})={str(maybe_new_value)} in library ({track_filename})"
                )
            return maybe_new_value

        track_filename: str = ""
        for field, length, value, data in item:
            if field == "pfil":
                assert isinstance(value, str)
                track_filename = os.path.normpath(value)

            rule = next((r for r in rules if field == r["field"]), None)
            if rule:
                rule["field_found"] = True  # type: ignore
                maybe_new_value = _maybe_perform_rule(rule, field, value)
                if maybe_new_value is not None:
                    value = maybe_new_value

            _dump(field, value, data)

        for rule in rules:
            if not rule["field_found"]:  # type: ignore
                field = rule["field"]
                maybe_new_value = _maybe_perform_rule(rule, field, None)
                if maybe_new_value is not None:
                    _dump(field, maybe_new_value, b"\x00")

    def modify_file(
        self,
        rules: list[ModifyRule],
        out_file: str | None = None,
        print_changes: bool = True,
    ):
        if out_file is None:
            out_file = self.filepath

        output = io.BytesIO()
        DatabaseV2._modify_data(output, list(self.data), rules, print_changes)

        with open(out_file, "wb") as write_file:
            write_file.write(output.getvalue())

    def to_objects(self) -> Generator[DbEntry]:
        for field, length, value, data in self.data:
            if isinstance(value, tuple):
                try:
                    new_val: list[DbEntry] = [
                        {
                            "field": f,
                            "field_name": DatabaseV2._get_field_name(f),
                            "size_bytes": l,
                            "value": v,
                        }
                        for f, l, v, d in value
                    ]
                except:
                    print(f"error on {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield {
                "field": field,
                "field_name": DatabaseV2._get_field_name(field),
                "size_bytes": length,
                "value": value,
            }

    def print_items(self):
        for entry in self.to_objects():
            if isinstance(entry["value"], list):
                print(
                    f"{entry['field']} ({entry['field_name']}, {entry['size_bytes']} B)"
                )
                for e in entry["value"]:
                    print(
                        f"    {e['field']} ({e['field_name']}, {e['size_bytes']} B): {e['value']}"
                    )
            else:
                print(
                    f"{entry['field']} ({entry['field_name']}, {entry['size_bytes']} B): {entry['value']}"
                )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=DatabaseV2.DEFAULT_DATABASE_FILE)
    args = parser.parse_args()

    db = DatabaseV2(args.file)
    db.print_items()
