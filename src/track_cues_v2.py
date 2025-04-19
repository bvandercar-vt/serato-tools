#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import base64
import configparser
import io
import logging
import struct
import sys
from typing import Any, Callable, NotRequired, Tuple, TypedDict

from mutagen.mp3 import MP3

from . import track_cues_v1
from .utils.tags import del_geob, get_geob, tag_geob

FMT_VERSION = "BB"

GEOB_KEY = "Serato Markers2"

CUE_COLORS = {
    k: bytes.fromhex(v)
    for k, v in {
        "red": "CC0000",  # Hot Cue 1
        "orange": "CC4400",
        "yelloworange": "CC8800",  # Hot Cue 2
        "yellow": "CCCC00",  # Hot Cue 4
        "limegreen1": "88CC00",
        "darkgreen": "44CC00",
        "limegreen2": "00CC00",  # Hot Cue 5
        "limegreen3": "00CC44",
        "seafoam": "00CC88",
        "cyan": "00CCCC",  # Hot Cue 7
        "lightblue": "0088CC",
        "blue1": "0044CC",
        "blue2": "0000CC",  # Hot Cue 3
        "purple1": "4400CC",
        "purple2": "8800CC",  # Hot Cue 8
        "pink": "CC00CC",  # Hot Cue 6
        "magenta": "CC0088",
        "pinkred": "CC0044",
    }.items()
}

TRACK_COLORS = {
    k: bytes.fromhex(v)
    for k, v in {
        "pink": "FF99FF",
        "darkpink": "FF99DD",
        "pinkred": "FF99BB",
        "red": "FF9999",
        "orange": "FFBB99",
        "yelloworange": "FFDD99",
        "yellow": "FFFF99",
        "limegreen1": "DDFF99",
        "limegreen2": "BBFF99",
        "limegreen3": "99FF99",
        "limegreen4": "99FFBB",
        "seafoam": "99FFDD",
        "cyan": "99FFFF",
        "lightblue": "99DDFF",
        "blue1": "99BBFF",
        "blue2": "9999FF",
        "purple": "BB99FF",
        "magenta": "DD99FF",
        "white": "FFFFFF",
        "grey": "BBBBBB",
        "black": "999999",
    }.items()
}


def get_cue_color_key(value: bytes) -> str | None:
    for key, v in CUE_COLORS.items():
        if v == value:
            return key
    return None


def get_track_color_key(value: bytes) -> str | None:
    for key, v in TRACK_COLORS.items():
        if v == value:
            return key
    return None


def readbytes(fp: io.BytesIO):
    for x in iter(lambda: fp.read(1), b""):
        if x == b"\00":
            break
        yield x


class Entry(object):
    NAME: str | None
    FIELDS: Tuple[str, ...]
    data: bytes

    def __init__(self, *args):
        assert len(args) == len(self.FIELDS)
        for field, value in zip(self.FIELDS, args):
            setattr(self, field, value)

    def __repr__(self):
        return "{name}({data})".format(
            name=self.__class__.__name__,
            data=", ".join(
                "{}={!r}".format(name, getattr(self, name)) for name in self.FIELDS
            ),
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
    FMT = "?"

    @classmethod
    def load(cls, data: bytes):
        return cls(*struct.unpack(cls.FMT, data))

    def dump(self):
        return struct.pack(self.FMT, *(getattr(self, f) for f in self.FIELDS))


class ColorEntry(Entry):
    NAME = "COLOR"
    FMT = "c3s"
    FIELDS = (
        "field1",
        "color",
    )

    @classmethod
    def load(cls, data: bytes):
        return cls(*struct.unpack(cls.FMT, data))

    def dump(self):
        return struct.pack(self.FMT, *(getattr(self, f) for f in self.FIELDS))


class CueEntry(Entry):
    NAME = "CUE"
    FMT = ">cBIc3s2s"
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
        info_size = struct.calcsize(cls.FMT)
        info = struct.unpack(cls.FMT, data[:info_size])
        name, nullbyte, other = data[info_size:].partition(b"\x00")
        assert nullbyte == b"\x00"
        assert other == b""
        return cls(*info, name.decode("utf-8"))

    def dump(self):
        struct_fields = self.FIELDS[:-1]
        return b"".join(
            (
                struct.pack(self.FMT, *(getattr(self, f) for f in struct_fields)),
                self.name.encode("utf-8"),
                b"\x00",
            )
        )


class LoopEntry(Entry):
    NAME = "LOOP"
    FMT = ">cBII4s4sB?"
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
        info_size = struct.calcsize(cls.FMT)
        info = struct.unpack(cls.FMT, data[:info_size])
        name, nullbyte, other = data[info_size:].partition(b"\x00")
        assert nullbyte == b"\x00"
        assert other == b""
        return cls(*info, name.decode("utf-8"))

    def dump(self):
        struct_fields = self.FIELDS[:-1]
        return b"".join(
            (
                struct.pack(self.FMT, *(getattr(self, f) for f in struct_fields)),
                self.name.encode("utf-8"),
                b"\x00",
            )
        )


class FlipEntry(Entry):
    NAME = "FLIP"
    FMT1 = "cB?"
    FMT2 = ">BI"
    FMT3 = ">BI16s"
    FIELDS = ("field1", "index", "enabled", "name", "loop", "num_actions", "actions")

    @classmethod
    def load(cls, data):
        info1_size = struct.calcsize(cls.FMT1)
        info1 = struct.unpack(cls.FMT1, data[:info1_size])
        name, nullbyte, other = data[info1_size:].partition(b"\x00")
        assert nullbyte == b"\x00"

        info2_size = struct.calcsize(cls.FMT2)
        loop, num_actions = struct.unpack(cls.FMT2, other[:info2_size])
        action_data = other[info2_size:]
        actions = []
        for i in range(num_actions):
            type_id, size = struct.unpack(cls.FMT2, action_data[:info2_size])
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


def get_entry_type(entry_name: str):
    for entry_cls in (BpmLockEntry, ColorEntry, CueEntry, LoopEntry, FlipEntry):
        if entry_cls.NAME == entry_name:
            return entry_cls
    return UnknownEntry


def parse(data: bytes):
    versionlen = struct.calcsize(FMT_VERSION)
    version = struct.unpack(FMT_VERSION, data[:versionlen])
    assert version == (0x01, 0x01)

    try:
        b64data = data[versionlen : data.index(b"\x00", versionlen)]
    except:
        b64data = data[versionlen:]
    b64data = b64data.replace(b"\n", b"")
    padding = b"A==" if len(b64data) % 4 == 1 else (b"=" * (-len(b64data) % 4))
    payload = base64.b64decode(b64data + padding)
    fp = io.BytesIO(payload)
    assert struct.unpack(FMT_VERSION, fp.read(2)) == (0x01, 0x01)
    while True:
        entry_name = b"".join(readbytes(fp)).decode("utf-8")
        if not entry_name:
            break
        entry_len = struct.unpack(">I", fp.read(4))[0]
        assert entry_len > 0

        entry_type = get_entry_type(entry_name)
        yield entry_type.load(fp.read(entry_len))


def dump(entries: list[Entry]):
    version = struct.pack(FMT_VERSION, 0x01, 0x01)

    contents = [version]
    for entry in entries:
        if entry.NAME is None:
            contents.append(entry.dump())
        else:
            data = entry.dump()
            contents.append(
                b"".join(
                    (
                        entry.NAME.encode("utf-8"),
                        b"\x00",
                        struct.pack(">I", (len(data))),
                        data,
                    )
                )
            )

    payload = b"".join(contents)
    payload_base64 = bytearray(base64.b64encode(payload).replace(b"=", b"A"))

    i = 72
    while i < len(payload_base64):
        payload_base64.insert(i, 0x0A)
        i += 73

    data = version
    data += payload_base64
    return data.ljust(470, b"\x00")


def parse_entries_file(contents: str, assert_len_1: bool):
    cp = configparser.ConfigParser()
    cp.read_string(contents)
    sections = tuple(sorted(cp.sections()))
    if assert_len_1:
        assert len(sections) == 1

    results: list[Entry] = []
    for section in sections:
        l, s, r = section.partition(": ")
        entry_type = get_entry_type(r if s else l)

        e = entry_type(
            *(
                ast.literal_eval(
                    cp.get(section, field),
                )
                for field in entry_type.FIELDS
            )
        )
        results.append(entry_type.load(e.dump()))
    return results


ValueType = bytes | str


class EntryModifyRule(TypedDict):
    field: str
    func: Callable[[ValueType], ValueType | None]


def modify_entry(
    entry: Entry,
    rules: list[EntryModifyRule],
    print_changes: bool = False,
):
    """
    Returns:
        entry: entry if was modified. If was not changed, returns None.
    """

    change_made = False

    output = f"[{entry.NAME}]\n"
    for field in entry.FIELDS:
        value = getattr(entry, field)

        for rule in rules:
            if field == rule["field"]:
                result = rule["func"](value)
                if result is not None:
                    value = result
                    change_made = True
                    if print_changes:
                        if isinstance(entry, ColorEntry):
                            print_val = (
                                get_track_color_key(value)
                                if isinstance(value, bytes)
                                else None
                            )
                            if not print_val:
                                print_val = f"Unknown Color ({str(value)})"
                            print(f"Set Track Color to {print_val}")
                        elif field == "color":
                            print_val = (
                                get_cue_color_key(value)
                                if isinstance(value, bytes)
                                else None
                            )
                            if not print_val:
                                print_val = f"Unknown Color ({str(value)})"
                            print(f"Set Cue Color to {print_val}")
                        else:
                            print(f'Set cue entry field "{field}" to {str(value)}')

        output += f"{field}: {value!r}\n"
    output += "\n"

    if not change_made:
        return None

    entry = parse_entries_file(output, assert_len_1=True)[0]
    return entry


class EntryModifyRules(TypedDict):
    cues: NotRequired[list[EntryModifyRule]]
    color: NotRequired[list[EntryModifyRule]]


def modify_file_entries(
    file: str | MP3,
    rules: EntryModifyRules,
    print_changes: bool = True,
    delete_tags_v1: bool = True,
):
    if isinstance(file, str):
        try:
            tags = MP3(file)
        except:
            logging.error("Mutagen error for file %s" % file)
            raise
    else:
        tags = file

    assert tags.filename, "must have filename"

    try:
        data = get_geob(tags, GEOB_KEY)
    except KeyError:
        logging.debug(
            f'File is missing "{GEOB_KEY}" tag, no cue points set yet', tags.filename
        )
        return

    if delete_tags_v1:
        del_geob(tags, track_cues_v1.GEOB_KEY)

    entries = list(parse(data))

    new_entries = []
    change_made = False
    for entry in entries:
        maybe_new_entry = None
        if "cues" in rules and isinstance(entry, CueEntry):
            maybe_new_entry = modify_entry(entry, rules["cues"], print_changes)
        elif "color" in rules and isinstance(entry, ColorEntry):
            maybe_new_entry = modify_entry(entry, rules["color"], print_changes)
        if maybe_new_entry is not None:
            entry = maybe_new_entry
            change_made = True
        new_entries.append(entry)

    if not change_made:
        return

    new_data = dump(new_entries)
    tag_geob(tags, GEOB_KEY, new_data)
    tags.save()


# TODO: allow color or key of colors dict
def set_track_color(
    file: str | MP3,
    color: bytes,
    print_changes: bool = True,
    delete_tags_v1: bool = True,
):
    modify_file_entries(
        file,
        {"color": [{"field": "color", "func": lambda v: color}]},
        print_changes,
        delete_tags_v1,
    )


def is_beatgrid_locked(entries: list[Entry]):
    any(
        (isinstance(entry, BpmLockEntry) and getattr(entry, "enabled"))
        for entry in entries
    )


if __name__ == "__main__":
    import argparse
    import math
    import subprocess
    import tempfile

    import mutagen._file

    from .utils.ui import get_hex_editor, get_text_editor, ui_ask

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

    if args.set_color:
        if args.set_color in TRACK_COLORS:
            set_track_color(args.file, TRACK_COLORS[args.set_color], print_changes=True)
        else:
            print(f"Track color must be one of: {str(list(TRACK_COLORS.keys()))}")
        sys.exit()

    if args.edit:
        text_editor = get_text_editor()
        hex_editor = get_hex_editor()

    tagfile = mutagen._file.File(args.file)
    if tagfile is not None:
        data = get_geob(tagfile, GEOB_KEY)
    else:
        with open(args.file, mode="rb") as fp:
            data = fp.read()

    entries = list(parse(data))
    new_entries: list[Entry] = []
    action = None

    width = math.floor(math.log10(len(entries))) + 1
    for entry_index, entry in enumerate(entries):
        if args.edit:
            if action not in ("q", "_"):
                print("{:{}d}: {!r}".format(entry_index, width, entry))
                action = ui_ask(
                    "Edit this entry",
                    {
                        "y": "edit this entry",
                        "n": "do not edit this entry",
                        "q": (
                            "quit; do not edit this entry or any of the "
                            "remaining ones"
                        ),
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
                            editor = hex_editor
                        else:
                            if action == "a":
                                entries_to_edit = (
                                    (
                                        "{:{}d}: {}".format(i, width, e.NAME),
                                        e,
                                    )
                                    for i, e in enumerate(
                                        entries[entry_index:], start=entry_index
                                    )
                                )
                            else:
                                entries_to_edit = ((entry.NAME, entry),)

                            for section, e in entries_to_edit:
                                f.write("[{}]\n".format(section).encode())
                                for field in e.FIELDS:
                                    f.write(
                                        "{}: {!r}\n".format(
                                            field,
                                            getattr(e, field),
                                        ).encode()
                                    )
                                f.write(b"\n")
                            editor = text_editor
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
                                results = parse_entries_file(
                                    output.decode(), assert_len_1=action != "a"
                                )
                            else:
                                results = [entry.load(output)]
                        except Exception as e:
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
        if new_entries == entries:
            print("No changes made.")
        else:
            new_data = dump(new_entries)

            if tagfile is not None:
                tag_geob(tagfile, GEOB_KEY, new_data)
                tagfile.save()
            else:
                with open(args.file, mode="wb") as fp:
                    fp.write(new_data)
