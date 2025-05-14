import os
import io
import struct
from typing import Iterable, TypedDict, Generator, Optional, cast
from enum import StrEnum

from serato_tools.utils import get_enum_key_from_value, logger, DataTypeError


class SeratoBinFile:
    class Fields(StrEnum):
        # Database & Crate
        VERSION = "vrsn"
        TRACK = "otrk"
        # Database
        FILE_TYPE = "ttyp"
        FILE_PATH = "pfil"
        TITLE = "tsng"
        ARTIST = "tart"
        ALBUM = "talb"
        GENRE = "tgen"
        LENGTH = "tlen"
        BITRATE = "tbit"
        SAMPLE_RATE = "tsmp"
        SIZE = "tsiz"
        BPM = "tbpm"
        KEY = "tkey"
        TIME = "utme"
        GROUPING = "tgrp"
        PUBLISHER = "tlbl"
        COMPOSER = "tcmp"
        YEAR = "ttyr"
        # Serato stuff
        DATE_ADDED_T = "tadd"
        DATE_ADDED_U = "uadd"
        BEATGRID_LOCKED = "bbgl"
        CORRUPT = "bcrt"
        MISSING = "bmis"
        # Crates
        SORTING = "osrt"
        REVERSE_ORDER = "brev"
        COLUMN = "ovct"
        COLUMN_NAME = "tvcn"
        COLUMN_WIDTH = "tvcw"
        TRACK_PATH = "ptrk"
        # Smart Crates
        SMARTCRATE_RULE = "rurt"
        SMARTCRATE_LIVE_UPDATE = "rlut"
        SMARTCRATE_MATCH_ALL = "rart"
        RULE_VALUE_TEXT = "trpt"
        RULE_VALUE_DATE = "trtt"
        RULE_VALUE_INTEGER = "urpt"
        RULE_COMPARISON = "trft"
        RULE_FIELD = "urkt"

    FIELDS = list(f.value for f in Fields)

    type KeyAndValue = tuple[Fields | str, "SeratoBinFile.Value"]
    type Struct = list[KeyAndValue]
    type Value = Struct | str | bytes | int | bool
    type ValueOrNone = Value | None

    type EntryFull = tuple[Fields | str, str, str | bytes | int | bool | list[EntryFull]]

    DEFAULT_DATA: Struct

    def __init__(self, file: str):
        self.filepath = os.path.abspath(file)
        self.dir = os.path.dirname(self.filepath)

        self.raw_data: bytes
        self.data: SeratoBinFile.Struct
        if os.path.exists(file):
            with open(file, "rb") as f:
                self.raw_data = f.read()
                self.data = list(SeratoBinFile._parse_item(self.raw_data))
        else:
            logger.warning(f"File does not exist: {file}. Using default data to create an empty item.")
            self.data = self.DEFAULT_DATA
            self._dump()

    def __str__(self):
        return str(list(self.to_entries()))

    def __repr__(self):
        return str(self.raw_data)

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == SeratoBinFile.Fields.VERSION else field[0]

    @staticmethod
    def _parse_item(item_data: bytes) -> Generator["SeratoBinFile.KeyAndValue", None, None]:
        fp = io.BytesIO(item_data)
        for header in iter(lambda: fp.read(8), b""):
            assert len(header) == 8
            field_ascii: bytes
            length: int
            field_ascii, length = struct.unpack(">4sI", header)
            field: str = field_ascii.decode("ascii")
            type_id: str = SeratoBinFile._get_type(field)

            data = fp.read(length)
            assert len(data) == length

            value: SeratoBinFile.Value
            if type_id in ("o", "r"):  #  struct
                value = list(SeratoBinFile._parse_item(data))
            elif type_id in ("p", "t"):  # text
                # value = (data[1:] + b"\00").decode("utf-16") # from imported code
                value = data.decode("utf-16-be")
            elif type_id == "b":  # single byte, is a boolean
                value = cast(bool, struct.unpack("?", data)[0])
            elif type_id == "s":  # signed int
                value = cast(int, struct.unpack(">H", data)[0])
            elif type_id == "u":  # unsigned int
                value = cast(int, struct.unpack(">I", data)[0])
            else:
                raise ValueError(f"unexpected type for field: {field}")

            yield field, value

    @staticmethod
    def _dump_item(field: str, value: Value) -> bytes:
        field_bytes = field.encode("ascii")
        assert len(field_bytes) == 4

        type_id: str = SeratoBinFile._get_type(field)

        if type_id in ("o", "r"):  #  struct
            if not isinstance(value, list):
                raise DataTypeError(value, list, field)
            data = SeratoBinFile._dump_struct(value)
        elif type_id in ("p", "t"):  # text
            if not isinstance(value, str):
                raise DataTypeError(value, str, field)
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
        return header + data

    @staticmethod
    def _dump_struct(item: Struct):
        return b"".join(SeratoBinFile._dump_item(field, value) for field, value in item)

    def _dump(self):
        self.raw_data = SeratoBinFile._dump_struct(self.data)

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath
        with open(file, "wb") as f:
            f.write(self.raw_data)

    @staticmethod
    def get_field_name(field: str) -> str:
        try:
            return (
                get_enum_key_from_value(field, SeratoBinFile.Fields)
                .replace("_", " ")
                .title()
                .replace("Smartcrate", "SmartCrate")
                .replace("Added U", "Added")
                .replace("Added T", "Added")
            )
        except ValueError:
            return "Unknown Field"

    @staticmethod
    def _check_valid_field(field: str):
        if field not in SeratoBinFile.FIELDS:
            raise ValueError(
                f"invalid field: {field} must be one of: {str(SeratoBinFile.FIELDS)}\n(see {__file__} for what these keys map to)"
            )

    @staticmethod
    def format_filepath(filepath: str) -> str:
        drive, filepath = os.path.splitdrive(filepath)  # pylint: disable=unused-variable
        return os.path.normpath(filepath).replace(os.path.sep, "/").lstrip("/")

    class __FieldObj(TypedDict):
        field: str

    @staticmethod
    def _check_rule_fields(rules: Iterable[__FieldObj]):
        all_field_names = [rule["field"] for rule in rules]
        uniq_field_names = list(set(all_field_names))
        assert len(list(rules)) == len(
            uniq_field_names
        ), f"must only have 1 function per field. fields passed: {str(sorted(all_field_names))}"
        for field in uniq_field_names:
            SeratoBinFile._check_valid_field(field)

    def to_entries(self) -> Generator[EntryFull, None, None]:
        for field, value in self.data:
            if isinstance(value, list):
                try:
                    new_val: list[SeratoBinFile.EntryFull] = []
                    for f, v in value:
                        if isinstance(v, list):
                            raise TypeError("not implemented for deeply nested")
                        new_val.append((f, SeratoBinFile.get_field_name(f), v))
                except:
                    logger.error(f"error on field: {field} value: {value}")
                    raise
                value = new_val
            else:
                value = repr(value)

            yield field, SeratoBinFile.get_field_name(field), value

    def print(self):
        for field, fieldname, value in self.to_entries():
            if isinstance(value, list):
                print(f"{field} ({fieldname})")
                for f, f_name, v in value:
                    if isinstance(v, list):
                        raise TypeError("unexpected type, deeply nested list")
                    print(f"    {f} ({f_name}): {str(v)}")
            else:
                print(f"{field} ({fieldname}): {str(value)}")
