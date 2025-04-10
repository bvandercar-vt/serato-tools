#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import struct
import sys
from typing import Any, Generator, TypedDict


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


def parse(fp: io.BytesIO | io.BufferedReader):
    for i, header in enumerate(iter(lambda: fp.read(8), b"")):
        assert len(header) == 8
        name_ascii: bytes
        length: int
        name_ascii, length = struct.unpack(">4sI", header)

        name: str = name_ascii.decode("ascii")
        type_id = "t" if name == "vrsn" else name[0] # vrsn field has no type_id, but contains text



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

        yield name, length, value


def parse_to_objects(fp: io.BytesIO | io.BufferedReader) -> Generator[DbEntry]:
    for name, length, value in parse(fp):
        if isinstance(value, tuple):
            new_val: list[DbEntry] = [
                {
                    "field": n,
                    "field_name": FIELDNAMES.get(n, "Unknown"),
                    "size_bytes": l,
                    "value": v,
                }
                for n, l, v in value
            ]
            value = new_val
        else:
            value = repr(value)

        yield {
            "field": name,
            "field_name": FIELDNAMES.get(name, "Unknown"),
            "size_bytes": length,
            "value": value,
        }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file", metavar="FILE", type=argparse.FileType("rb"))
    args = parser.parse_args(argv)

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
