#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import logging
import os
import struct
from typing import Tuple, overload

StructType = list[Tuple[str, "ValueType"]]
ValueType = StructType | str | bytes


class Crate(object):
    TRACK_FIELD = "otrk"
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

    def __init__(self, fname):
        self.data: StructType = []

        self.path: str = os.path.dirname(os.path.abspath(fname))
        self.filename: str = os.path.basename(fname)

        # Omit the _Serato_ and Subcrates folders at the end
        self.track_path: str = os.path.join(*Crate._split_path(self.path)[:-2])

        if os.path.exists(fname):
            self.load_from_file(fname)
        else:
            logging.error(f"file does not exist: {fname}. Using default data.")
            self.data = Crate.DEFAULT_DATA

    def __str__(self):
        tracks = self.tracks()
        return f"Crate containing {len(tracks)} tracks: \n{'\n'.join(tracks)}"

    def print_data(self):
        from pprint import pprint

        pprint(self.data)

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
            os.path.join(self.track_path, track_name), self.track_path
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

    class DataTypeError(Exception):
        def __init__(self, data: ValueType, expected_type: type, tag: str | None):
            super().__init__(
                f"data must be {expected_type.__name__} when tag is {tag} (type: {type(data).__name__})"
            )

   

    @overload
    @staticmethod
    def _parse(data: bytes, tag: None = None) -> StructType: ...
    @overload
    @staticmethod
    def _parse(data: bytes, tag: str) -> ValueType: ...
    @staticmethod
    def _parse(data: bytes, tag: str | None = None) -> ValueType | StructType:
        if tag == None or tag[0] == "o":  #  struct
            ret_data: StructType = []
            i = 0
            while i < len(data):
                tag = data[i : i + 4].decode("ascii")
                length = struct.unpack(">I", data[i + 4 : i + 8])[0]
                value = data[i + 8 : i + 8 + length]
                value = Crate._parse(value, tag=tag)
                ret_data.append((tag, value))
                i += 8 + length
            return ret_data
        elif tag == "vrsn" or tag[0] in ["t", "p"]:  # version or text
            return data.decode("utf-16-be")
        elif tag == "sbav" or tag[0] == "b":  # signed or bytes
            return data
        elif tag[0] == "u":  # unsigned
            ret_val: bytes = struct.unpack(">I", data)[0]
            return ret_val
        else:
            raise ValueError(f"unexpected value for tag: {tag}")


    @staticmethod
    def _dump(data: ValueType, tag: str | None = None) -> bytes:
        if tag == None or tag[0] == "o":  # struct
            if not isinstance(data, list):
                raise Crate.DataTypeError(data, list, tag)
            ret_data = bytes()
            for dat in data:
                tag = dat[0]
                value = Crate._dump(dat[1], tag=tag)
                length = struct.pack(">I", len(value))
                ret_data = ret_data + tag.encode("utf-8") + length + value
            return ret_data
        elif tag == "vrsn" or tag[0] in ["t", "p"]:  # version or text
            if not isinstance(data, str):
                raise Crate.DataTypeError(data, str, tag)
            return data.encode("utf-16-be")
        elif tag == "sbav" or tag[0] == "b":  # signed or bytes
            if isinstance(data, str):
                return data.encode("utf-8")
            else:
                if not isinstance(data, bytes):
                    raise Crate.DataTypeError(data, bytes, tag)
                return data
        elif tag[0] == "u":  #  unsigned
            return struct.pack(">I", data)
        else:
            raise ValueError(f"unexpected value for tag: {tag}")

    def load_from_file(self, fname: str):
        with open(fname, "rb") as mfile:
            self.data = Crate._parse(mfile.read())

    def save_to_file(self, fname: str | None = None):
        if fname is None:
            fname = os.path.join(self.path, self.filename)

        enc_data = Crate._dump(self.data)
        with open(fname, "wb") as mfile:
            mfile.write(enc_data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("-f", "--filenames_only", action="store_true")
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
    else:
        print(crate)

    if args.output_file:
        crate.save_to_file(args.output_file)
