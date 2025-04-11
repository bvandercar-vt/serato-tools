#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import struct
from typing import Optional, Tuple


def _decode(data: bytes, tag: Optional[str] = None, reverse: bool = False):
    if tag == None or tag[0] == "o":
        # decode struct
        if reverse:
            ret_data = bytes()
            for dat in data:
                tag = dat[0]
                value = _decode(dat[1], tag=tag, reverse=reverse)
                length = struct.pack(">I", len(value))
                ret_data = ret_data + tag.encode("utf-8") + length + value

            return ret_data
        else:
            ret_data = []
            i = 0
            while i < len(data):
                tag = data[i : i + 4].decode("ascii")
                length = struct.unpack(">I", data[i + 4 : i + 8])[0]
                value = data[i + 8 : i + 8 + length]
                value = _decode(value, tag=tag)
                ret_data.append((tag, value))
                i += 8 + length
            return ret_data
    elif tag == "vrsn" or tag[0] in ["t", "p"]:
        # decode unicode
        return data.encode("utf-16-be") if reverse else data.decode("utf-16-be")
    elif tag == "sbav" or tag[0] == "b":
        # noop, is bytes
        return data.encode("utf-8") if reverse and isinstance(data, str) else data
    elif tag[0] == "u":
        # decode unsigned
        return struct.pack(">I", data) if reverse else struct.unpack(">I", data)[0]
    else:
        raise ValueError(f"unexpected value for tag: {tag}")


def _split_path(path):
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


class Crate(object):
    def __init__(self, fname):
        self.data: list[Tuple[str, str | list[tuple[str, str]]]] = []

        self.crate_path = os.path.dirname(os.path.abspath(fname))
        self.name = os.path.basename(fname)

        if os.path.exists(fname):
            self.load_from_file(fname)
        else:
            self.data = [
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

    def __str__(self):
        tracks = self.tracks()
        st = "Crate containing {} tracks: \n".format(len(tracks))
        st += "\n".join(tracks)
        return st

    def print_data(self):
        from pprint import PrettyPrinter

        printer = PrettyPrinter(indent=4)
        printer.pprint(self.data)

    def tracks(self):
        return [dat[1][0][1] for dat in self.data if dat[0] == "otrk"]

    def track_path(self):
        # Omit the _Serato_ and Subcrates folders at the end
        return os.path.join(*_split_path(self.crate_path)[:-2])

    def remove_track(self, track_name):
        # track_name needs to include the containing folder name.
        for i, dat in enumerate(self.data):
            if dat[0] == "otrk" and dat[1][0][1] == track_name:
                self.data.pop(i)
                return True

        return False

    def add_track(self, track_name):
        # track name must include the containing folder name
        track_name = os.path.relpath(
            os.path.join(self.track_path(), track_name), self.track_path()
        )

        if track_name in self.tracks():
            return False

        self.data.append(("otrk", [("ptrk", track_name)]))
        return True

    def include_tracks_from_folder(self, folder_path):
        """
        Make this crate include all and only the files in the given folder
        """
        folder_tracks = os.listdir(folder_path)
        folder_tracks = [
            os.path.join(os.path.split(folder_path)[1], trck) for trck in folder_tracks
        ]

        for track in self.tracks():
            if track not in folder_tracks:
                self.remove_track(track)

        for mfile in folder_tracks:
            self.add_track(mfile)

    def load_from_file(self, fname):
        with open(fname, "rb") as mfile:
            self.data = _decode(mfile.read())

    def save_to_file(self, fname=None):
        if fname is None:
            fname = os.path.join(self.crate_path, self.name)

        enc_data = _decode(self.data, reverse=True)
        with open(fname, "wb") as mfile:
            mfile.write(enc_data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("-f", "--filenames_only", action="store_true")
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
