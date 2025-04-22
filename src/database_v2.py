#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import struct
import sys
from typing import (Any, Callable, Generator, Iterable, NotRequired, Tuple,
                    TypedDict)


class DbEntry(TypedDict):
    field: str
    field_name: str
    value: str | int | bool | list["DbEntry"]
    size_bytes: int


ParsedType = Tuple[str, int, Any, bytes]


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
    def _get_field_name(name: str):
        return DatabaseV2.FIELDNAMES.get(name, "Unknown Field")

    @staticmethod
    def _get_type(name: str) -> str:
        # vrsn field has no type_id, but contains text
        return "t" if name == "vrsn" else name[0]

    def _parse(
        self, fp: io.BytesIO | io.BufferedReader | str | None
    ) -> Generator[ParsedType]:
        if fp is None:
            fp = self.filepath
        if isinstance(fp, str):
            fp = open(fp, "rb")

        for header in iter(lambda: fp.read(8), b""):
            assert len(header) == 8
            name_ascii: bytes
            length: int
            name_ascii, length = struct.unpack(">4sI", header)
            name: str = name_ascii.decode("ascii")
            type_id: str = DatabaseV2._get_type(name)

            data = fp.read(length)
            assert len(data) == length

            value: bytes | str | tuple
            if type_id == "b":
                value = struct.unpack("?", data)[0]
            elif type_id in ("o", "r"):
                value = tuple(self._parse(io.BytesIO(data)))
            elif type_id in ("p", "t"):
                value = (data[1:] + b"\00").decode("utf-16")
            elif type_id == "s":
                value = struct.unpack(">H", data)[0]
            elif type_id == "u":
                value = struct.unpack(">I", data)[0]
            else:
                value = data

            yield name, length, value, data

    class ModifyRule(TypedDict):
        field: str
        func: Callable[[str, Any], Any]
        files: NotRequired[list[str]]

    @staticmethod
    def _modify_data(
        fp: io.BytesIO | io.BufferedWriter,
        item: Iterable[ParsedType],
        rules: list[ModifyRule] = [],
        print_changes: bool = False,
    ):
        for rule in rules:
            if "files" in rule:
                rule["files"] = [
                    os.path.normpath(os.path.splitdrive(file)[1]).lstrip("\\").upper()
                    for file in rule["files"]
                ]

        track_filename: str = ""
        for name, length, value, data in item:
            name_bytes = name.encode("ascii")
            assert len(name_bytes) == 4

            type_id: str = DatabaseV2._get_type(name)

            if name == "pfil":
                assert isinstance(value, str)
                track_filename = os.path.normpath(value)

            rule_has_been_done = False
            for rule in rules:
                if name == rule["field"] and (
                    "files" not in rule or track_filename.upper() in rule["files"]
                ):
                    maybe_new_value = rule["func"](track_filename, value)
                    if maybe_new_value is not None:
                        assert (
                            not rule_has_been_done
                        ), f"Should only pass one rule per field (field: {name})"
                        rule_has_been_done = True
                        value = maybe_new_value
                        if print_changes:
                            print(
                                f"Set {name} ({DatabaseV2._get_field_name(name)})={str(value)} in library"
                            )

            if type_id == "b":
                data = struct.pack("?", value)
            elif type_id in ("o", "r"):
                assert isinstance(value, tuple)
                nested_buffer = io.BytesIO()
                DatabaseV2._modify_data(nested_buffer, value, rules, print_changes)
                data = nested_buffer.getvalue()
            elif type_id in ("p", "t"):
                new_data = str(value).encode("utf-16")[2:]
                assert new_data[-1:] == b"\x00"
                data = data[:1] + new_data[:-1]
            elif type_id == "s":
                data = struct.pack(">H", value)
            elif type_id == "u":
                data = struct.pack(">I", value)

            length = len(data)

            header = struct.pack(">4sI", name_bytes, length)
            fp.write(header)
            fp.write(data)

    def modify_file(
        self,
        rules: list[ModifyRule],
        out_file: str | None = None,
        print_changes: bool = False,
    ):
        if out_file is None:
            out_file = self.filepath

        output = io.BytesIO()
        DatabaseV2._modify_data(output, list(self.data), rules, print_changes)

        with open(out_file, "wb") as write_file:
            write_file.write(output.getvalue())

    def to_objects(self) -> Generator[DbEntry]:
        for name, length, value, data in self.data:
            if isinstance(value, tuple):
                try:
                    new_val: list[DbEntry] = [
                        {
                            "field": n,
                            "field_name": DatabaseV2._get_field_name(n),
                            "size_bytes": l,
                            "value": v,
                        }
                        for n, l, v, d in value
                    ]
                except:
                    print(f"error on {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield {
                "field": name,
                "field_name": DatabaseV2._get_field_name(name),
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
