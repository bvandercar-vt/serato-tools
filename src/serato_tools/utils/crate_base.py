#!/usr/bin/python
# This is from this repo: https://github.com/sharst/seratopy
import os
import sys
from typing import Optional, Callable

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.bin_file_base import SeratoBinFile
from serato_tools.utils import SERATO_DIR, DataTypeError


class CrateBase(SeratoBinFile):
    EXTENSION: str
    DIR: str

    def __init__(self, file: str):
        super().__init__(file=file)

    class Track(SeratoBinFile.Track):
        def __init__(self, data: "CrateBase.Struct"):
            super().__init__(data, filepath_key=CrateBase.Fields.TRACK_PATH)

    def track_paths(self) -> list[str]:
        track_paths: list[str] = []
        for field, value in self.data:
            if field == CrateBase.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = CrateBase.Track(value)
                track_paths.append(track.filepath)
        return track_paths

    def save(self, file: Optional[str] = None):
        if file is None:
            file = self.filepath

        if not file.endswith(self.EXTENSION):
            raise ValueError(f"file should end with {self.EXTENSION}: " + file)

        super().save(file)

    def process_tracks(self, func: Callable[[str], str]):
        for i, (field, value) in enumerate(self.data):
            if field == CrateBase.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = CrateBase.Track(value)
                maybe_new_path = func(track.filepath)
                if maybe_new_path != track.filepath:
                    track.set_value(CrateBase.Fields.TRACK_PATH, maybe_new_path)
                    self.data[i] = (field, track.to_struct())

    def filter_tracks(self, func: Callable[[str], bool]):
        for i, (field, value) in enumerate(self.data):
            if field == CrateBase.Fields.TRACK:
                if not isinstance(value, list):
                    raise DataTypeError(value, list, field)
                track = CrateBase.Track(value)
                if not func(track.filepath):
                    self.data.pop(i)

    def remove_track(self, filepath: str):
        # filepath name must include the containing dir
        self.filter_tracks(lambda fpath: fpath != filepath)

    def add_track(self, filepath: str):
        # filepath name must include the containing dir
        filepath = self.format_filepath(filepath)

        if filepath in self.track_paths():
            return

        self.data.append((CrateBase.Fields.TRACK, [(CrateBase.Fields.TRACK_PATH, filepath)]))

    def add_tracks_from_dir(self, dir: str, replace: bool = False):
        dir_tracks = [self.format_filepath(os.path.join(dir, t)) for t in os.listdir(dir)]

        if replace:
            for track in self.track_paths():
                if track not in dir_tracks:
                    self.remove_track(track)

        for track in dir_tracks:
            self.add_track(track)

    def remove_duplicates(self):
        track_names: list[str] = []

        def filter_track(fname: str) -> bool:
            track_names.append(fname)
            return fname not in track_names

        self.filter_tracks(filter_track)

    @classmethod
    def list_dir(cls):
        DIR = os.path.join(SERATO_DIR, cls.DIR)
        for file in os.listdir(DIR):
            print(os.path.join(DIR, file))
