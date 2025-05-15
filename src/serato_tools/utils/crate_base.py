#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import SERATO_DIR


class CrateBase(SeratoBinFile):
    EXTENSION: str
    DIR: str

    def __init__(self, file: str):
        super().__init__(file=file, track_path_key=CrateBase.Fields.TRACK_PATH)

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith(self.EXTENSION):
            raise ValueError(f"file should end with {self.EXTENSION}: " + file)

        self._dump()
        super().save(file)

    def add_track(self, filepath: str):
        # filepath name must include the containing dir
        filepath = self.format_filepath(filepath)

        if filepath in self.get_track_paths():
            return

        self.data.append((CrateBase.Fields.TRACK, [(CrateBase.Fields.TRACK_PATH, filepath)]))

    def add_tracks_from_dir(self, dir: str, replace: bool = False):
        dir_tracks = [self.format_filepath(os.path.join(dir, t)) for t in os.listdir(dir)]

        if replace:
            for track in self.get_track_paths():
                if track not in dir_tracks:
                    self.remove_track(track)

        for track in dir_tracks:
            self.add_track(track)

    @classmethod
    def list_dir(cls):
        DIR = os.path.join(SERATO_DIR, cls.DIR)
        for file in os.listdir(DIR):
            print(os.path.join(DIR, file))
