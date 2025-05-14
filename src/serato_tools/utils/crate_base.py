#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import logger


class CrateBase(SeratoBinFile):
    DEFAULT_DATA: SeratoBinFile.Struct

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
                self.data = list(CrateBase._parse_item(self.raw_data))
        else:
            logger.warning(f"File does not exist: {file}. Using default data for an empty crate.")
            self.data = self.DEFAULT_DATA
            self.raw_data = b""

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
    def _get_track_name(value: "CrateBase.Value") -> str:
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

        self._dump()
        with open(file, "wb") as f:
            f.write(self.raw_data)
