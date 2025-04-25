import os
from typing import Any, Iterable

from . import to_array


class SeratoBinDb:
    FIELDNAMES = {
        # Database & Crate
        "vrsn": "Version",
        "otrk": "Track",
        # Database
        "ttyp": "File Type",
        "pfil": "File Path",
        "tsng": "Song Title",
        "tart": "Artist",
        "talb": "Album",
        "tgen": "Genre",
        "tlen": "Length",
        "tbit": "Bitrate",
        "tsmp": "Sample Rate",
        "tsiz": "Size",
        "tbpm": "BPM",
        "tkey": "Key",
        "tart": "Artist",
        "utme": "File Time",
        "tgrp": "Grouping",
        "tlbl": "Publisher",
        "tcmp": "Composer",
        "ttyr": "Year",
        # Serato stuff
        "tadd": "Date added",
        "uadd": "Date added",
        "bbgl": "Beatgrid Locked",
        "bcrt": "Corrupt",
        "bmis": "Missing",
        # Crates
        "osrt": "Sorting",
        "brev": "Reverse Order",
        "ovct": "Column",
        "tvcn": "Column Name",
        "tvcw": "Column Width",
        "ptrk": "Track Path",
    }
    TRACK_FIELD = "otrk"

    class DataTypeError(Exception):
        def __init__(
            self, value: Any, expected_type: type | Iterable[type], field: str | None
        ):
            super().__init__(
                f"value must be {' or '.join(e.__name__ for e in to_array(expected_type))} when field is {field} (type: {type(value).__name__}) (value: {str(value)})"
            )

    @staticmethod
    def get_field_name(field: str):
        return SeratoBinDb.FIELDNAMES.get(field, "Unknown Field")

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == "vrsn" else field[0]

    @staticmethod
    def remove_drive_from_filepath(filepath: str) -> str:
        return os.path.normpath(os.path.splitdrive(filepath)[1]).lstrip("\\")
