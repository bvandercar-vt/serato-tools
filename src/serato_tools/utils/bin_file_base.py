import os
from typing import Iterable, TypedDict, Generator
from enum import StrEnum

from serato_tools.utils import get_enum_key_from_value, logger


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

    raw_data: bytes
    data: Struct

    def __repr__(self):
        return str(self.raw_data)

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
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == SeratoBinFile.Fields.VERSION else field[0]

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
