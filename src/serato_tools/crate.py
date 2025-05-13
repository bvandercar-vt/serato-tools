#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import struct
import sys
from typing import Generator, TypedDict, Union, overload

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.database import SeratoBinDb
from serato_tools.utils import logger, DataTypeError


class Crate(SeratoBinDb):
    DEFAULT_DATA = [
        ("vrsn", "1.0/Serato ScratchLive Crate"),
        ("osrt", [("tvcn", "key"), ("brev", "\x00")]),
        ("ovct", [("tvcn", "song"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "playCount"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "artist"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "bpm"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "key"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "album"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "length"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "comment"), ("tvcw", "0")]),
        ("ovct", [("tvcn", "added"), ("tvcw", "0")]),
    ]

    StructType = list[tuple[str, "ValueType"]]
    ValueType = StructType | str | bytes

    ValueOrNoneType = Union[ValueType, None]

    def __init__(self, file: str):
        self.filepath = os.path.abspath(file)
        self.dir = os.path.dirname(self.filepath)

        # Omit the _Serato_ and Subcrates folders at the end
        self.track_dir: str = os.path.join(*Crate._split_path(self.dir)[:-2])

        self.raw_data: bytes
        self.data: Crate.StructType
        if os.path.exists(file):
            with open(file, "rb") as f:
                self.raw_data = f.read()
                self.data = self._parse_item(self.raw_data)
        else:
            logger.warning(
                f"File does not exist: {file}. Using default data for an empty crate."
            )
            self.data = Crate.DEFAULT_DATA
            self.raw_data = b""

    def __str__(self):
        tracks = self.tracks()
        return f"Crate containing {len(tracks)} tracks: \n{'\n'.join(tracks)}"

    @overload
    @staticmethod
    def _parse_item(data: bytes, field: None = None) -> StructType: ...
    @overload
    @staticmethod
    def _parse_item(data: bytes, field: str) -> ValueType: ...
    @staticmethod
    def _parse_item(data: bytes, field: str | None = None) -> ValueType | StructType:
        if not isinstance(data, bytes):
            raise DataTypeError(data, bytes, field)

        type_id: str = Crate._get_type(field) if field else "o"
        if type_id == "o":  # struct
            ret_data: Crate.StructType = []
            i = 0
            while i < len(data):
                field = data[i : i + 4].decode("ascii")
                length = struct.unpack(">I", data[i + 4 : i + 8])[0]
                value = data[i + 8 : i + 8 + length]
                value = Crate._parse_item(value, field=field)
                ret_data.append((field, value))
                i += 8 + length
            return ret_data
        elif type_id in ("p", "t"):  # text
            return data.decode("utf-16-be")
        elif type_id == "b":  # single byte
            return data
        elif type_id == "u":  # unsigned int
            ret_val: bytes = struct.unpack(">I", data)[0]
            return ret_val
        else:
            raise ValueError(f"unexpected type for field: {field}")

    def _dump(self) -> bytes:
        def _dump_item(data: Crate.ValueType, field: str | None = None) -> bytes:
            type_id: str = Crate._get_type(field) if field else "o"
            if type_id == "o":  # struct
                if not isinstance(data, list):
                    raise DataTypeError(data, list, field)
                ret_data = bytes()
                for dat in data:
                    field = dat[0]
                    value = _dump_item(dat[1], field=field)
                    length = struct.pack(">I", len(value))
                    ret_data = ret_data + field.encode("utf-8") + length + value
                return ret_data
            elif type_id in ("p", "t"):  # text
                if not isinstance(data, str):
                    raise DataTypeError(data, str, field)
                return data.encode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                # if isinstance(data, str) return data.encode("utf-8") # from imported code, but have never seen this happen.
                if not isinstance(data, bytes):
                    raise DataTypeError(data, bytes, field)
                return data
            elif type_id == "u":  #  unsigned
                if not isinstance(data, bytes):
                    raise DataTypeError(data, bytes, field)
                return struct.pack(">I", data)
            else:
                raise ValueError(f"unexpected type for field: {field}")

        return _dump_item(self.data, None)

    @staticmethod
    def _split_path(path: str):
        allparts = []
        while True:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    @staticmethod
    def _get_track_name(value: ValueType) -> str:
        if not isinstance(value, list):
            raise TypeError(f"{Crate.TRACK_FIELD} should be list")
        track_name = value[0][1]
        if not isinstance(track_name, str):
            raise TypeError(f"value should be str")
        return track_name

    def tracks(self) -> list[str]:
        track_names: list[str] = []
        for dat in self.data:
            if dat[0] == Crate.TRACK_FIELD:
                track_name = Crate._get_track_name(dat[1])
                track_names.append(track_name)
        return track_names

    def remove_track(self, track_name: str):
        # track_name needs to include the containing folder name.
        found = False
        for i, dat in enumerate(self.data):
            if dat[0] == Crate.TRACK_FIELD:
                crate_track_name = Crate._get_track_name(dat[1])
                if crate_track_name == track_name:
                    self.data.pop(i)
                    found = True

        if not found:
            raise ValueError(f"Track not found in crate: {track_name}")

    def add_track(self, track_name: str):
        # track name must include the containing folder name
        track_name = os.path.relpath(
            os.path.join(self.track_dir, track_name), self.track_dir
        )

        if track_name in self.tracks():
            return

        self.data.append((Crate.TRACK_FIELD, [("ptrk", track_name)]))

    def include_tracks_from_folder(self, folder_path: str, replace: bool = False):
        folder_tracks = os.listdir(folder_path)
        folder_tracks = [
            os.path.join(os.path.split(folder_path)[1], track)
            for track in folder_tracks
        ]

        if replace:
            for track in self.tracks():
                if track not in folder_tracks:
                    self.remove_track(track)

        for mfile in folder_tracks:
            self.add_track(mfile)

    def save(self, file: str | None = None):
        if file is None:
            file = self.filepath

        raw_data = self._dump()
        with open(file, "wb") as f:
            f.write(raw_data)
        self.raw_data = raw_data

    class EntryDict(TypedDict):
        field: str
        field_name: str
        value: Union["Crate.ValueType", list["Crate.EntryDict"]]

    def to_dicts(self) -> Generator[EntryDict, None, None]:
        for field, value in self.data:
            if isinstance(value, list):
                try:
                    new_val: list[Crate.EntryDict] = [
                        {
                            "field": f,
                            "field_name": Crate.get_field_name(f),
                            "value": v,
                        }
                        for f, v in value
                    ]
                except:
                    logger.error(f"error on {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield {
                "field": field,
                "field_name": Crate.get_field_name(field),
                "value": value,
            }

    def print(self):
        for entry in self.to_dicts():
            if isinstance(entry["value"], list):
                field_lines = []
                for e in entry["value"]:
                    if isinstance(e, tuple):
                        raise TypeError("unexpected type")
                    field_lines.append(
                        f"[ {e['field']} ({e['field_name']}): {e['value']} ]"
                    )
                print_val = ", ".join(field_lines)
            else:
                print_val = entry["value"]
            print(f"{entry['field']} ({entry['field_name']}): {print_val}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("-f", "--filenames_only", action="store_true")
    parser.add_argument("-d", "--data", action="store_true")
    parser.add_argument(
        "-o", "--output", "--output_file", dest="output_file", default=None
    )
    args = parser.parse_args()

    crate = Crate(args.file)
    tracks = crate.tracks()
    if args.filenames_only:
        track_names = [
            os.path.splitext(os.path.basename(track))[0] for track in crate.tracks()
        ]
        print("\n".join(track_names))
    elif args.data:
        crate.print()
    else:
        print(crate)

    if args.output_file:
        crate.save(args.output_file)
