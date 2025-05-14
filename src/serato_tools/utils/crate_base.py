#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import struct
import sys
from typing import Generator, Union, overload, cast, Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import logger, DataTypeError


class CrateBase(SeratoBinFile):
    type Struct = list[tuple[str, "CrateBase.Value"]]
    type Value = Union[Struct, str, bytes, bool]

    type ValueOrNone = Union[Value, None]

    DEFAULT_DATA: Struct

    def __init__(self, file: str):
        self.filepath = os.path.abspath(file)
        self.dir = os.path.dirname(self.filepath)

        # Omit the _Serato_ and Subcrates folders at the end
        self.track_dir: str = os.path.join(*CrateBase._split_path(self.dir)[:-2])

        self.raw_data: bytes
        self.data: CrateBase.Struct
        if os.path.exists(file):
            with open(file, "rb") as f:
                self.raw_data = f.read()
                self.data = self._parse_item(self.raw_data)
        else:
            logger.warning(f"File does not exist: {file}. Using default data for an empty crate.")
            self.data = self.DEFAULT_DATA
            self.raw_data = b""

    @overload
    @staticmethod
    def _parse_item(data: bytes, field: None = None) -> Struct: ...
    @overload
    @staticmethod
    def _parse_item(data: bytes, field: str) -> Value: ...
    @staticmethod
    def _parse_item(data: bytes, field: Optional[str] = None) -> Union[Value, Struct]:
        if not isinstance(data, bytes):
            raise DataTypeError(data, bytes, field)

        type_id: str = CrateBase._get_type(field) if field else "o"
        if type_id in ("o", "r"):  # struct
            ret_data: CrateBase.Struct = []
            i = 0
            while i < len(data):
                field = data[i : i + 4].decode("ascii")
                length = struct.unpack(">I", data[i + 4 : i + 8])[0]
                value = data[i + 8 : i + 8 + length]
                value = CrateBase._parse_item(value, field=field)
                ret_data.append((field, value))
                i += 8 + length
            return ret_data
        elif type_id in ("p", "t"):  # text
            return data.decode("utf-16-be")
        elif type_id == "b":  # single byte
            return cast(bool, struct.unpack("?", data)[0])
        elif type_id == "u":  # unsigned int
            return cast(bytes, struct.unpack(">I", data)[0])
        else:
            raise ValueError(f"unexpected type for field: {field}")

    def _dump(self) -> bytes:
        def _dump_item(data: CrateBase.Value, field: Optional[str] = None) -> bytes:
            type_id: str = CrateBase._get_type(field) if field else "o"
            if type_id == "o":  # struct
                if not isinstance(data, list):
                    raise DataTypeError(data, list, field)
                ret_data = bytes()
                for dat in data:
                    dat_field = dat[0]
                    value = _dump_item(dat[1], field=dat_field)
                    length = struct.pack(">I", len(value))
                    ret_data = ret_data + dat_field.encode("utf-8") + length + value
                return ret_data
            elif type_id in ("p", "t"):  # text
                if not isinstance(data, str):
                    raise DataTypeError(data, str, field)
                return data.encode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                # if isinstance(data, str) return data.encode("utf-8") # from imported code, but have never seen this happen.
                if not isinstance(data, bool):
                    raise DataTypeError(data, bytes, field)
                return struct.pack("?", data)
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
    def _get_track_name(value: Value) -> str:
        if not isinstance(value, list):
            raise TypeError(f"{CrateBase.Fields.TRACK} should be list")
        track_name = value[0][1]
        if not isinstance(track_name, str):
            raise TypeError("value should be str")
        return track_name

    def tracks(self) -> list[str]:
        track_names: list[str] = []
        for dat in self.data:
            if dat[0] == CrateBase.Fields.TRACK:
                track_name = CrateBase._get_track_name(dat[1])
                track_names.append(track_name)
        return track_names

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith("crate"):
            raise ValueError("file should end with crate: " + file)

        raw_data = self._dump()
        with open(file, "wb") as f:
            f.write(raw_data)
        self.raw_data = raw_data

    type EntryFull = tuple[str, str, Union["CrateBase.Value", list["CrateBase.EntryFull"]]]

    def to_entries(self) -> Generator[EntryFull, None, None]:
        for field, value in self.data:
            if isinstance(value, list):
                try:
                    new_val: list[CrateBase.EntryFull] = [(f, CrateBase.get_field_name(f), v) for f, v in value]
                except:
                    logger.error(f"error on {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield field, CrateBase.get_field_name(field), value
