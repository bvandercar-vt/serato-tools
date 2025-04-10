#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import struct
import sys
from typing import Any, Callable, Generator, Iterable, Tuple, TypedDict

DATABASE_FILE = os.path.join(os.path.expanduser("~"), "Music\\_Serato_\\database V2")


class DbEntry(TypedDict):
    field: str
    field_name: str
    value: str | int | bool | list["DbEntry"]
    size_bytes: int


FIELDNAMES = {
    # Database
    "vrsn": "Version",
    "otrk": "Track",
    "ttyp": "File Type",
    "pfil": "File Path",
    "tsng": "Song Title",
    "tlen": "Length",
    "tbit": "Bitrate",
    "tsmp": "Sample Rate",
    "tbpm": "BPM",
    "tadd": "Date added",
    "uadd": "Date added",
    "tkey": "Key",
    "bbgl": "Beatgrid Locked",
    "tart": "Artist",
    "utme": "File Time",
    "bmis": "Missing",
    # Crates
    "osrt": "Sorting",
    "brev": "Reverse Order",
    "ovct": "Column Title",
    "tvcn": "Column Name",
    "tvcw": "Column Width",
    "ptrk": "Track Path",
}


def _get_type_id(name: str) -> str:
    # vrsn field has no type_id, but contains text
    return "t" if name == "vrsn" else name[0]


ParsedType = Tuple[str, int, Any, bytes]


def parse(fp: io.BytesIO | io.BufferedReader) -> Generator[ParsedType]:
    for header in iter(lambda: fp.read(8), b""):
        assert len(header) == 8
        name_ascii: bytes
        length: int
        name_ascii, length = struct.unpack(">4sI", header)
        name: str = name_ascii.decode("ascii")
        type_id: str = _get_type_id(name)

        data = fp.read(length)
        assert len(data) == length

        value: Any
        if type_id == "b":
            value = struct.unpack("?", data)[0]
        elif type_id in ("o", "r"):
            value = tuple(parse(io.BytesIO(data)))
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


def modify(
    fp: io.BytesIO | io.BufferedWriter,
    parsed: Iterable[ParsedType],
    rules: list[ModifyRule] = [],
):
    track_filename: str = ""
    for name, length, value, data in parsed:
        name_bytes = name.encode("ascii")
        assert len(name_bytes) == 4

        type_id: str = _get_type_id(name)

        if name == "pfil":
            assert isinstance(value, str)
            track_filename = os.path.normpath(value)

        rule_has_been_done = False
        for rule in rules:
            if name == rule["field"]:
                maybe_new_value = rule["func"](track_filename, value)
                if maybe_new_value is not None:
                    assert (
                        not rule_has_been_done
                    ), f"Should only pass one rule per field (field: {name})"
                    rule_has_been_done = True
                    value = maybe_new_value

        if type_id == "b":
            data = struct.pack("?", value)
        elif type_id in ("o", "r"):
            assert isinstance(value, tuple)
            nested_buffer = io.BytesIO()
            modify(nested_buffer, value, rules)
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


def modify_file(file: str, rules: list[ModifyRule]):
    with open(file, "rb") as read_file:
        parsed = list(parse(read_file))

    output = io.BytesIO()
    modify(output, parsed, rules)

    with open(file, "wb") as write_file:
        output.seek(0)
        write_file.write(output.read())


def parse_to_objects(fp: io.BytesIO | io.BufferedReader | str) -> Generator[DbEntry]:
    if isinstance(fp, str):
        fp = open(fp, "rb")

    for name, length, value, data in parse(fp):
        if isinstance(value, tuple):
            try:
                new_val: list[DbEntry] = [
                    {
                        "field": n,
                        "field_name": FIELDNAMES.get(n, "Unknown"),
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
            "field_name": FIELDNAMES.get(name, "Unknown"),
            "size_bytes": length,
            "value": value,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=argparse.FileType("rb"),
        default=open(DATABASE_FILE, "rb"),
        nargs="?",
    )
    args = parser.parse_args()

    for entry in parse_to_objects(args.file):
        if isinstance(entry["value"], list):
            print(f"{entry['field']} ({entry['field_name']}, {entry['size_bytes']} B)")
            for e in entry["value"]:
                print(
                    f"    {e['field']} ({e['field_name']}, {e['size_bytes']} B): {e['value']}"
                )
        else:
            print(
                f"{entry['field']} ({entry['field_name']}, {entry['size_bytes']} B): {entry['value']}"
            )
