#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import base64
import configparser
import io
import os
import struct
import sys
from typing import Callable, TypedDict, Literal, List, Sequence, Union, NotRequired
from enum import Enum

from mutagen.mp3 import HeaderNotFoundError

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.track_cues_v1 import TrackCuesV1
from serato_tools.utils import get_enum_key_from_value, logger, DataTypeError
from serato_tools.utils.track_tags import SeratoTag


class TrackCuesV2(SeratoTag):
    GEOB_KEY = "Serato Markers2"
    VERSION = (0x01, 0x01)

    class CueColors(Enum):
        RED = b"\xcc\x00\x00"
        ORANGE = b"\xcc\x44\x00"
        YELLOWORANGE = b"\xcc\x88\x00"
        YELLOW = b"\xcc\xcc\x00"
        LIMEGREEN1 = b"\x88\xcc\x00"
        DARKGREEN = b"\x44\xcc\x00"
        LIMEGREEN2 = b"\x00\xcc\x00"
        LIMEGREEN3 = b"\x00\xcc\x88"
        SEAFOAM = b"\x00\xcc\x88"
        CYAN = b"\x00\xcc\xcc"
        LIGHTBLUE = b"\x00\x88\xcc"
        BLUE1 = b"\x00\x44\xcc"
        BLUE2 = b"\x00\x00\xcc"
        PURPLE1 = b"\x44\x00\xcc"
        PURPLE2 = b"\x88\x00\xcc"
        PINK = b"\xcc\x00\xcc"
        MAGENTA = b"\xcc\x00\x88"
        PINKRED = b"\xcc\x00\x44"

    class TrackColors(Enum):
        PINK = b"\xff\x99\xff"
        DARKPINK = b"\xff\x99\xdd"
        PINKRED = b"\xff\x99\xbb"
        RED = b"\xff\x99\x99"
        ORANGE = b"\xff\xbb\x99"
        YELLOWORANGE = b"\xff\xdd\x99"
        YELLOW = b"\xff\xff\x99"
        LIMEGREEN1 = b"\xdd\xff\x99"
        LIMEGREEN2 = b"\xbb\xff\x99"
        LIMEGREEN3 = b"\x99\xff\x99"
        LIMEGREEN4 = b"\x99\xff\xbb"
        SEAFOAM = b"\x99\xff\xdd"
        CYAN = b"\x99\xff\xff"
        LIGHTBLUE = b"\x99\xdd\xff"
        BLUE1 = b"\x99\xbb\xff"
        BLUE2 = b"\x99\x99\xff"
        PURPLE = b"\xbb\x99\xff"
        MAGENTA = b"\xdd\x99\xff"
        WHITE = b"\xff\xff\xff"
        GREY = b"\xbb\xbb\xbb"
        BLACK = b"\x99\x99\x99"

    def __init__(self, file_or_data: SeratoTag.FileOrData):
        self.raw_data: bytes | None = None
        super().__init__(file_or_data)

        self.entries: list[TrackCuesV2.Entry] = []
        if self.raw_data is not None:
            self.entries = list(self._parse(self.raw_data))
        self.modified: bool = False

    @staticmethod
    def _get_cue_color_key(value: bytes) -> str:
        return get_enum_key_from_value(value, TrackCuesV2.CueColors)

    @staticmethod
    def _get_track_color_key(value: bytes) -> str:
        return get_enum_key_from_value(value, TrackCuesV2.TrackColors)

    @staticmethod
    def _get_entry_class(entry_name: str):
        return next(
            (
                cls
                for cls in (
                    TrackCuesV2.BpmLockEntry,
                    TrackCuesV2.ColorEntry,
                    TrackCuesV2.CueEntry,
                    TrackCuesV2.LoopEntry,
                    TrackCuesV2.FlipEntry,
                )
                if cls.NAME == entry_name
            ),
            TrackCuesV2.UnknownEntry,
        )

    class Entry(object):
        NAME: str | None
        FIELDS: tuple[str, ...]
        data: bytes

        def __init__(self, *args):
            assert len(args) == len(self.FIELDS)
            for field, value in zip(self.FIELDS, args):
                setattr(self, field, value)

        def __repr__(self) -> str:
            return "{name}({data})".format(
                name=self.__class__.__name__,
                data=", ".join("{}={!r}".format(name, getattr(self, name)) for name in self.FIELDS),
            )

        @classmethod
        def load(cls, data: bytes):
            return cls(data)

        def dump(self) -> bytes:
            return self.data

    class UnknownEntry(Entry):
        NAME = None
        FIELDS = ("data",)

        @classmethod
        def load(cls, data: bytes):
            return cls(data)

        def dump(self):
            return self.data

    class BpmLockEntry(Entry):
        NAME = "BPMLOCK"
        FIELDS = ("enabled",)
        FORMAT = "?"

        @classmethod
        def load(cls, data: bytes):
            return cls(*struct.unpack(cls.FORMAT, data))

        def dump(self):
            return struct.pack(self.FORMAT, *(getattr(self, f) for f in self.FIELDS))

    class ColorEntry(Entry):
        NAME = "COLOR"
        FORMAT = "c3s"
        FIELDS = (
            "field1",
            "color",
        )

        @classmethod
        def load(cls, data: bytes):
            return cls(*struct.unpack(cls.FORMAT, data))

        def dump(self):
            return struct.pack(self.FORMAT, *(getattr(self, f) for f in self.FIELDS))

    class CueEntry(Entry):
        NAME = "CUE"
        FORMAT = ">cBIc3s2s"
        FIELDS = (
            "field1",
            "index",
            "position",
            "field4",
            "color",
            "field6",
            "name",
        )
        name: str

        @classmethod
        def load(cls, data: bytes):
            info_size = struct.calcsize(cls.FORMAT)
            info = struct.unpack(cls.FORMAT, data[:info_size])
            name, nullbyte, other = data[info_size:].partition(b"\x00")
            assert nullbyte == b"\x00"
            assert other == b""
            return cls(*info, name.decode("utf-8"))

        def dump(self):
            struct_fields = self.FIELDS[:-1]
            return b"".join(
                (
                    struct.pack(self.FORMAT, *(getattr(self, f) for f in struct_fields)),
                    self.name.encode("utf-8"),
                    b"\x00",
                )
            )

    class LoopEntry(Entry):
        NAME = "LOOP"
        FORMAT = ">cBII4s4sB?"
        FIELDS = (
            "field1",
            "index",
            "startposition",
            "endposition",
            "field5",
            "field6",
            "color",
            "locked",
            "name",
        )
        name: str

        @classmethod
        def load(cls, data: bytes):
            info_size = struct.calcsize(cls.FORMAT)
            info = struct.unpack(cls.FORMAT, data[:info_size])
            name, nullbyte, other = data[info_size:].partition(b"\x00")
            assert nullbyte == b"\x00"
            assert other == b""
            return cls(*info, name.decode("utf-8"))

        def dump(self):
            struct_fields = self.FIELDS[:-1]
            return b"".join(
                (
                    struct.pack(self.FORMAT, *(getattr(self, f) for f in struct_fields)),
                    self.name.encode("utf-8"),
                    b"\x00",
                )
            )

    class FlipEntry(Entry):
        NAME = "FLIP"
        FORMAT1 = "cB?"
        FORMAT2 = ">BI"
        FORMAT3 = ">BI16s"
        FIELDS = (
            "field1",
            "index",
            "enabled",
            "name",
            "loop",
            "num_actions",
            "actions",
        )

        @classmethod
        def load(cls, data):
            info1_size = struct.calcsize(cls.FORMAT1)
            info1 = struct.unpack(cls.FORMAT1, data[:info1_size])
            name, nullbyte, other = data[info1_size:].partition(b"\x00")
            assert nullbyte == b"\x00"

            info2_size = struct.calcsize(cls.FORMAT2)
            loop, num_actions = struct.unpack(cls.FORMAT2, other[:info2_size])
            action_data = other[info2_size:]
            actions = []
            for i in range(num_actions):  # pylint: disable=unused-variable
                type_id, size = struct.unpack(cls.FORMAT2, action_data[:info2_size])
                action_data = action_data[info2_size:]
                if type_id == 0:
                    payload = struct.unpack(">dd", action_data[:size])
                    actions.append(("JUMP", *payload))
                elif type_id == 1:
                    payload = struct.unpack(">ddd", action_data[:size])
                    actions.append(("CENSOR", *payload))
                action_data = action_data[size:]
            assert action_data == b""

            return cls(*info1, name.decode("utf-8"), loop, num_actions, actions)

        def dump(self):
            raise NotImplementedError("FLIP entry dumps are not implemented!")

    def _parse(self, data: bytes):
        self._check_version(data[: self.VERSION_LEN])
        data = data[self.VERSION_LEN :]  # b64data
        try:
            end_index = data.index(b"\x00")
            data = data[:end_index]
        except ValueError:
            pass  # data = data
        data = data.replace(b"\n", b"")
        padding = b"A==" if len(data) % 4 == 1 else (b"=" * (-len(data) % 4))
        payload = base64.b64decode(data + padding)
        fp = io.BytesIO(payload)
        self._check_version(fp.read(self.VERSION_LEN))
        while True:
            entry_name = SeratoTag._readbytes(fp).decode("utf-8")
            if not entry_name:
                break
            entry_len = struct.unpack(">I", fp.read(4))[0]
            assert entry_len > 0

            entry_class = TrackCuesV2._get_entry_class(entry_name)
            yield entry_class.load(fp.read(entry_len))

    def _dump(self):
        version = self._pack_version()

        contents: list[bytes] = [version]
        for entry in self.entries:
            data = entry.dump()
            if entry.NAME is not None:
                data = b"".join(
                    (
                        entry.NAME.encode("utf-8"),
                        b"\x00",
                        struct.pack(">I", (len(data))),
                        data,
                    )
                )
            contents.append(data)

        payload = b"".join(contents)
        payload_base64 = bytearray(base64.b64encode(payload).replace(b"=", b"A"))

        i = 72
        while i < len(payload_base64):
            payload_base64.insert(i, 0x0A)
            i += 73

        data = version
        data += payload_base64

        new_raw_data = data.ljust(470, b"\x00")

        self.modified = new_raw_data != self.raw_data  # pylint: disable=access-member-before-definition
        self.raw_data = new_raw_data

    @staticmethod
    def parse_entries_file(contents: str, assert_len_1: bool):
        cp = configparser.ConfigParser()
        cp.read_string(contents)
        sections: Sequence[str] = tuple(sorted(cp.sections()))
        if assert_len_1:
            assert len(sections) == 1

        results: list[TrackCuesV2.Entry] = []
        for section in sections:
            l, s, r = section.partition(": ")
            entry_class = TrackCuesV2._get_entry_class(r if s else l)

            e = entry_class(
                *(
                    ast.literal_eval(
                        cp.get(section, field),
                    )
                    for field in entry_class.FIELDS
                )
            )
            results.append(entry_class.load(e.dump()))
        return results

    type Value = bytes | str | int

    class EntryModifyRule(TypedDict):
        field: str
        func: Callable[["TrackCuesV2.Value"], Union["TrackCuesV2.Value", None]]
        """ (prev_value: ValueType) -> new_value: ValueType | None """

    class CueIndexModifyRule(EntryModifyRule):
        field: Literal["index"]  # pyright: ignore[reportIncompatibleVariableOverride]
        func: Callable[[int], int | None]
        """ (prev_value: ValueType) -> new_value: ValueType | None """

    class CueColorModifyRule(EntryModifyRule):
        field: Literal["color"]  # pyright: ignore[reportIncompatibleVariableOverride]
        func: Callable[["TrackCuesV2.CueColors"], Union["TrackCuesV2.CueColors", None]]
        """ (prev_value: ValueType) -> new_value: ValueType | None """

    class CueNameModifyRule(EntryModifyRule):
        field: Literal["name"]  # pyright: ignore[reportIncompatibleVariableOverride]
        func: Callable[[str], str | None]
        """ (prev_value: ValueType) -> new_value: ValueType | None """

    class TrackColorModifyRule(EntryModifyRule):
        field: Literal["color"]  # pyright: ignore[reportIncompatibleVariableOverride]
        func: Callable[["TrackCuesV2.TrackColors"], Union["TrackCuesV2.TrackColors", None]]
        """ (prev_value: ValueType) -> new_value: ValueType | None """

    type CueRules = CueIndexModifyRule | CueColorModifyRule | CueNameModifyRule | EntryModifyRule
    type TrackColorRules = TrackColorModifyRule | EntryModifyRule

    class EntryModifyRules(TypedDict):
        cues: NotRequired[List["TrackCuesV2.CueRules"]]
        color: NotRequired[List["TrackCuesV2.TrackColorRules"]]

    FIELD_TO_TYPE_MAP = {"color": bytes, "index": int, "name": str}

    @staticmethod
    def _modify_entry(entry: Entry, rules: Sequence[CueRules | TrackColorRules]):
        """
        Returns:
            entry: entry if was modified. If was not changed, returns None.
        """

        all_field_names = [rule["field"] for rule in rules]
        assert len(rules) == len(
            list(set(all_field_names))
        ), f"must only have 1 function per field. fields passed: {str(sorted(all_field_names))}"
        # TODO: ensure field is valid else throw error!

        change_made = False

        output = f"[{entry.NAME}]\n"
        for field in entry.FIELDS:
            value: TrackCuesV2.Value = getattr(entry, field)

            rule = next((r for r in rules if field == r["field"]), None)
            if rule:
                ExpectedType: type | None = TrackCuesV2.FIELD_TO_TYPE_MAP.get(field, None)
                if ExpectedType and not isinstance(value, ExpectedType):
                    raise DataTypeError(value, ExpectedType, field)

                prev_value = value
                if field == "color":
                    is_track_color = isinstance(entry, TrackCuesV2.ColorEntry)
                    Colors = TrackCuesV2.TrackColors if is_track_color else TrackCuesV2.CueColors
                    try:
                        prev_value = Colors(prev_value)
                    except ValueError:
                        pass

                maybe_new_val = rule["func"](prev_value)  # type: ignore
                if isinstance(maybe_new_val, Enum):
                    maybe_new_val = maybe_new_val.value
                if maybe_new_val is not None and maybe_new_val != value:
                    value = maybe_new_val

                    if ExpectedType and not isinstance(value, ExpectedType):
                        raise DataTypeError(value, ExpectedType, field)

                    change_made = True

                    if field == "color":
                        is_track_color = isinstance(entry, TrackCuesV2.ColorEntry)
                        color_name: str | None = None
                        if isinstance(value, bytes):
                            get_color_name = (
                                TrackCuesV2._get_track_color_key if is_track_color else TrackCuesV2._get_cue_color_key
                            )
                            try:
                                color_name = get_color_name(value)
                            except ValueError:
                                color_name = None
                        color_log_str = "Track" if is_track_color else "Cue"
                        logger.info(
                            f"Set {color_log_str} Color to {color_name if color_name else f'Unknown Color ({str(value)})'}"
                        )
                    else:
                        logger.info(f'Set {type(entry).__name__} field "{field}" to {str(value)}')
            output += f"{field}: {value!r}\n"
        output += "\n"

        if not change_made:
            return None

        entry = TrackCuesV2.parse_entries_file(output, assert_len_1=True)[0]
        return entry

    def modify_entries(self, rules: EntryModifyRules, delete_tags_v1: bool = True):
        """
        Args:
            delete_tags_v1: Must delete delete_tags_v1 in order for many tags_v2 changes appear in Serato (since we never change tags_v1 along with it (TODO)). Not sure what tags_v1 is even for, probably older versions of Serato. Have found no issues with deleting this, but use with caution if running an older version of Serato.
        """
        if delete_tags_v1 and self.tagfile:
            super(SeratoTag, self)._del_geob(TrackCuesV1.GEOB_KEY)  # pylint: disable=bad-super-call

        new_entries = []
        change_made = False
        for entry in self.entries:
            maybe_new_entry = None
            if "cues" in rules and isinstance(entry, TrackCuesV2.CueEntry):
                maybe_new_entry = TrackCuesV2._modify_entry(entry, rules["cues"])
            elif "color" in rules and isinstance(entry, TrackCuesV2.ColorEntry):
                maybe_new_entry = TrackCuesV2._modify_entry(entry, rules["color"])
            if maybe_new_entry is not None:
                entry = maybe_new_entry
                change_made = True
            new_entries.append(entry)

        if not change_made:
            return

        self.entries = new_entries
        self._dump()

    def save(self, force: bool = False):
        if self.modified or force:
            super().save()

    def get_track_color(self) -> bytes | None:
        color_entry = next(
            (entry for entry in self.entries if isinstance(entry, TrackCuesV2.ColorEntry)),
            None,
        )
        if color_entry is None:
            return None
        return getattr(color_entry, "color")

    def get_track_color_name(self) -> str | None:
        color_bytes = self.get_track_color()
        if color_bytes is None:
            return None
        return self._get_track_color_key(color_bytes)

    def set_track_color(self, color: TrackColors, delete_tags_v1: bool = True):
        """
        Args:
            color: TrackColors (bytes)
            delete_tags_v1: Must delete delete_tags_v1 in order for track color change to appear in Serato (since we never change tags_v1 along with it (TODO)). Not sure what tags_v1 is even for, probably older versions of Serato. Have found no issues with deleting this, but use with caution if running an older version of Serato.
        """
        self.modify_entries({"color": [{"field": "color", "func": lambda v: color}]}, delete_tags_v1)

    def is_beatgrid_locked(self) -> bool:
        return any(
            (isinstance(entry, TrackCuesV2.BpmLockEntry) and getattr(entry, "enabled")) for entry in self.entries
        )


if __name__ == "__main__":
    import argparse
    import math
    import subprocess
    import tempfile

    from serato_tools.utils.ui import get_hex_editor, get_text_editor, ui_ask

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument(
        "--set_color",
        dest="set_color",
        default=None,
        help="Set track color",
    )
    parser.add_argument("-e", "--edit", action="store_true")
    args = parser.parse_args()

    try:
        tags = TrackCuesV2(args.file)
    except HeaderNotFoundError:
        with open(args.file, mode="rb") as fp:
            data = fp.read()
        tags = TrackCuesV2(data)

    if args.set_color:
        tags.set_track_color(args.set_color)
        tags.save()
        sys.exit()

    if args.edit:
        text_editor = get_text_editor()
        hex_editor = get_hex_editor()

    new_entries: list[TrackCuesV2.Entry] = []
    width = math.floor(math.log10(len(tags.entries))) + 1
    action = None
    for entry_index, entry in enumerate(tags.entries):
        if args.edit:
            if action not in ("q", "_"):
                print("{:{}d}: {!r}".format(entry_index, width, entry))
                action = ui_ask(
                    "Edit this entry",
                    {
                        "y": "edit this entry",
                        "n": "do not edit this entry",
                        "q": ("quit; do not edit this entry or any of the " "remaining ones"),
                        "a": "edit this entry and all later entries in the file",
                        "b": "edit raw bytes",
                        "r": "remove this entry",
                    },
                    default="n",
                )

            if action in ("y", "a", "b"):
                while True:
                    with tempfile.NamedTemporaryFile() as f:
                        if action == "b":
                            f.write(entry.dump())
                            editor = hex_editor  # pyright: ignore[reportPossiblyUnboundVariable]
                        else:
                            if action == "a":
                                entries_to_edit = (
                                    (
                                        "{:{}d}: {}".format(i, width, e.NAME),
                                        e,
                                    )
                                    for i, e in enumerate(tags.entries[entry_index:], start=entry_index)
                                )
                            else:
                                entries_to_edit = ((entry.NAME, entry),)

                            for section, e in entries_to_edit:
                                f.write("[{}]\n".format(section).encode())
                                for field in e.FIELDS:
                                    f.write("{}: {!r}\n".format(field, getattr(e, field)).encode())
                                f.write(b"\n")
                            editor = text_editor  # pyright: ignore[reportPossiblyUnboundVariable]
                        f.flush()
                        status = subprocess.call((editor, f.name))
                        f.seek(0)
                        output = f.read()

                    if status != 0:
                        if (
                            ui_ask(
                                "Command failed, retry",
                                {
                                    "y": "edit again",
                                    "n": "leave unchanged",
                                },
                            )
                            == "n"
                        ):
                            break
                    else:
                        try:
                            if action != "b":
                                results = TrackCuesV2.parse_entries_file(output.decode(), assert_len_1=action != "a")
                            else:
                                results = [entry.load(output)]
                        except Exception as e:  # pylint: disable=broad-exception-caught
                            print(str(e))
                            if (
                                ui_ask(
                                    "Content seems to be invalid, retry",
                                    {
                                        "y": "edit again",
                                        "n": "leave unchanged",
                                    },
                                )
                                == "n"
                            ):
                                break
                        else:
                            for i, e in enumerate(results, start=entry_index):
                                print("{:{}d}: {!r}".format(i, width, e))
                            subaction = ui_ask(
                                "Above content is valid, save changes",
                                {
                                    "y": "save current changes",
                                    "n": "discard changes",
                                    "e": "edit again",
                                },
                                default="y",
                            )
                            if subaction == "y":
                                new_entries.extend(results)
                                if action == "a":
                                    action = "_"
                                break
                            elif subaction == "n":
                                if action == "a":
                                    action = "q"
                                new_entries.append(entry)
                                break
            elif action in ("r", "_"):
                continue
            else:
                new_entries.append(entry)
        else:
            print("{:{}d}: {!r}".format(entry_index, width, entry))

    if args.edit:
        if new_entries == tags.entries:
            print("No changes made.")
        else:
            tags.entries = new_entries
            tags._dump()  # pylint: disable=protected-access
            if tags.tagfile:
                tags.save()
            else:
                with open(args.file, mode="wb") as fp:
                    fp.write(tags.raw_data or b"")
