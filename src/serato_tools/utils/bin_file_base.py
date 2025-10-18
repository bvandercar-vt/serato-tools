import os
import io
import re
import struct
import base64
from typing import Iterable, TypedDict, Generator, Optional, cast, Callable, Pattern
from enum import StrEnum

from serato_tools.utils import get_enum_key_from_value, logger, DataTypeError, DeeplyNestedListError


class SeratoBinFile:
    class Fields(StrEnum):
        # Database & Crate
        VERSION = "vrsn"
        TRACK = "otrk"
        # Database - Track
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
        DATE_ADDED_T = "tadd"
        DATE_ADDED_U = "uadd"
        BEATGRID_LOCKED = "bbgl"
        CORRUPT = "bcrt"
        MISSING = "bmis"
        HAS_STEMS = "bstm"
        PLAYED = "bply"
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

    type ParsedField = Fields | str
    type BasicValue = str | bytes | int | bool

    type Entry = tuple[ParsedField, "SeratoBinFile.Value"]
    type EntryList = list[Entry]
    type Value = BasicValue | EntryList

    type EntryFull = tuple[ParsedField, str, "SeratoBinFile.EntryFullValue"]
    type EntryFullList = list[EntryFull]
    type EntryFullValue = BasicValue | EntryFullList

    type ValueOrNone = Value | None

    DEFAULT_ENTRIES: EntryList

    def __init__(self, file: str, track_path_key: "SeratoBinFile.Fields"):
        self.filepath = os.path.abspath(file)
        self.dir = os.path.dirname(self.filepath)
        self.TRACK_PATH_KEY = track_path_key

        self.raw_data: bytes
        self.entries: SeratoBinFile.EntryList
        if os.path.exists(file):
            with open(file, "rb") as f:
                self.raw_data = f.read()
                self.entries = list(SeratoBinFile._parse_item(self.raw_data))
        else:
            logger.warning(f"File does not exist: {file}. Using default data to create an empty item.")
            self.entries = self.DEFAULT_ENTRIES
            self._dump()

    def __str__(self) -> str:
        return self._stringify_entries(self.get_entries())

    def _stringify_entries(self, entries: Iterable[EntryFull], indent: int = 0) -> str:
        lines: list[str] = []
        indent_str = "    " * indent

        for field, fieldname, value in entries:
            if isinstance(value, list):
                lines.append(f"{indent_str}{field} ({fieldname})")
                lines.append(self._stringify_entries(value, indent + 1))
            else:
                lines.append(f"{indent_str}{field} ({fieldname}): {str(value)}")

        return "\n".join(lines)

    class EntryJson(TypedDict):
        field: "SeratoBinFile.ParsedField"
        fieldname: str
        type: str
        value: str | int | bool | list["SeratoBinFile.EntryJson"]

    def to_json_object(self) -> list[EntryJson]:
        def entries_to_json(entries: SeratoBinFile.EntryList) -> list[SeratoBinFile.EntryJson]:
            result = []

            for field, value in entries:
                if isinstance(value, list):
                    value = entries_to_json(value)
                elif isinstance(value, (bytes, bytearray, memoryview)):
                    value = base64.b64encode(value).decode("utf-8")  # need to make JSON compatible

                entry_obj: SeratoBinFile.EntryJson = {
                    "field": field,
                    "fieldname": SeratoBinFile.get_field_name(field),
                    "value": value,
                    "type": type(value).__name__,
                }

                result.append(entry_obj)

            return result

        return entries_to_json(self.entries)

    def write_json(self, filepath: str) -> None:
        import json

        def write_json_array(f, json_entries: list[SeratoBinFile.EntryJson], indent: int = 0) -> None:
            indent_str = "  " * indent
            f.write("[\n")

            for i, entry in enumerate(json_entries):
                if isinstance(entry["value"], list):
                    f.write(
                        f'{indent_str}  {{"field": "{entry["field"]}", "fieldname": "{entry["fieldname"]}", "type": "{entry["type"]}", "value": '
                    )
                    write_json_array(f, entry["value"], indent + 1)
                    f.write("}")
                else:
                    f.write(f"{indent_str}  {json.dumps(entry, ensure_ascii=False)}")

                if i < len(json_entries) - 1:
                    f.write(",\n")
                else:
                    f.write("\n")

            f.write(f"{indent_str}]")

        with open(filepath, "w", encoding="utf-8") as f:
            write_json_array(f, self.to_json_object(), indent=0)

    def print(self):
        print(self)

    def __repr__(self) -> str:
        return str(self.raw_data)

    class EntryListCls:
        def __init__(self, entries: "SeratoBinFile.EntryList"):
            self.fields: list[str] = []

            for field, value in entries:
                if isinstance(value, list):
                    raise DeeplyNestedListError
                setattr(self, field, value)
                self.fields.append(field)

        def __repr__(self) -> str:
            return str(self.to_entries())

        def get_value(self, field: str) -> "SeratoBinFile.Value":
            return getattr(self, field)

        def set_value(self, field: str, value: "SeratoBinFile.Value"):
            if field not in self.fields:
                self.fields.append(field)
            setattr(self, field, value)

        def to_entries(self) -> "SeratoBinFile.EntryList":
            return [(f, self.get_value(f)) for f in self.fields]

    class Track(EntryListCls):
        def __init__(self, entries: "SeratoBinFile.EntryList", track_path_key: str):
            super().__init__(entries)

            self.track_path_key = track_path_key
            track_path = self.get_value(track_path_key)
            if not isinstance(track_path, str):
                raise DataTypeError(track_path, str, track_path_key)
            self.path: str = track_path

        def set_path(self, path: str):
            self.set_value(self.track_path_key, path)
            self.path = path

    def _get_track(self, entries: "SeratoBinFile.EntryList"):
        return SeratoBinFile.Track(entries, track_path_key=self.TRACK_PATH_KEY)

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == SeratoBinFile.Fields.VERSION else field[0]

    @staticmethod
    def _parse_item(item_data: bytes) -> Generator["SeratoBinFile.Entry", None, None]:
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
    def _dump_item(entry: Entry) -> bytes:
        field, value = entry
        field_bytes = field.encode("ascii")
        assert len(field_bytes) == 4

        type_id: str = SeratoBinFile._get_type(field)

        if type_id in ("o", "r"):  #  struct (list)
            if not isinstance(value, list):
                raise DataTypeError(value, list, field)
            data = SeratoBinFile._dump_entries(value)
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
    def _dump_entries(entries: EntryList):
        return b"".join(SeratoBinFile._dump_item(entry) for entry in entries)

    def _dump(self):
        self.raw_data = SeratoBinFile._dump_entries(self.entries)

    def get_track_paths(self) -> list[str]:
        track_paths: list[str] = []
        for field, value in self.entries:
            if field == SeratoBinFile.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = self._get_track(value)
                track_paths.append(track.path)
        return track_paths

    def modify_tracks(self, func: Callable[[Track], Track]):
        for i, (field, value) in enumerate(self.entries):
            if field == SeratoBinFile.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = self._get_track(value)
                new_track = func(track)
                self.entries[i] = (field, new_track.to_entries())
        self._dump()

    def filter_tracks(self, func: Callable[[Track], bool]):
        new_entries: "SeratoBinFile.EntryList" = []
        for field, value in self.entries:
            if field == SeratoBinFile.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = self._get_track(value)
                if not func(track):
                    continue
            new_entries.append((field, value))
        self.entries = new_entries
        self._dump()

    def remove_track(self, filepath: str):
        # filepath name must include the containing dir
        self.filter_tracks(lambda track: track.path != filepath)

    def remove_duplicates(self):
        track_paths: list[str] = []

        def filter_track(track: "SeratoBinFile.Track") -> bool:
            was_in_track_paths = track.path not in track_paths
            track_paths.append(track.path)
            return was_in_track_paths

        self.filter_tracks(filter_track)

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

    def get_entries(self) -> Generator[EntryFull, None, None]:
        """Get entry fieldnames."""
        yield from self.__get_entries_internal(track_matcher=None)

    def get_entries_filtered(self, track_matcher: str | Pattern[str]) -> Generator[EntryFull, None, None]:
        """Get entry fieldnames with track matching filter."""
        yield from self.__get_entries_internal(track_matcher=track_matcher)

    def __get_entries_internal(self, track_matcher: Optional[str | Pattern[str]]) -> Generator[EntryFull, None, None]:
        """Internal implementation for getting entry fieldnames."""
        for field, value in self.entries:
            if isinstance(value, list):
                if track_matcher and field == SeratoBinFile.Fields.TRACK:
                    if not isinstance(value, list):
                        raise DataTypeError(value, list, field)
                    track = self.__class__.Track(value, track_path_key=self.TRACK_PATH_KEY)
                    if not bool(re.search(track_matcher, track.path, re.IGNORECASE)):
                        continue

                try:
                    new_entries: list[SeratoBinFile.EntryFull] = []
                    for f, v in value:
                        if isinstance(v, list):
                            raise DeeplyNestedListError
                        new_entries.append((f, SeratoBinFile.get_field_name(f), v))
                except:
                    logger.error(f"error on field: {field} value: {value}")
                    raise
                value = new_entries

            yield field, SeratoBinFile.get_field_name(field), value
