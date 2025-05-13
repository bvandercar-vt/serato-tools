import os
from typing import Iterable, TypedDict


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
    FIELDNAME_KEYS = list(FIELDNAMES.keys())
    TRACK_FIELD = "otrk"

    raw_data: bytes

    def __repr__(self):
        return self.raw_data

    @staticmethod
    def get_field_name(field: str):
        return SeratoBinDb.FIELDNAMES.get(field, "Unknown Field")

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == "vrsn" else field[0]

    @staticmethod
    def _check_valid_field(field: str):
        if field not in SeratoBinDb.FIELDNAME_KEYS:
            raise ValueError(
                f"invalid field: {field} must be one of: {str(SeratoBinDb.FIELDNAME_KEYS)}\n(see {__file__} for what these keys map to)"
            )

    @staticmethod
    def remove_drive_from_filepath(filepath: str) -> tuple[str, str]:
        drive, filepath = os.path.splitdrive(filepath)
        return os.path.normpath(filepath).lstrip("\\"), drive

    class FieldObj(TypedDict):
        field: str

    @staticmethod
    def _check_rule_fields(rules: Iterable[FieldObj]):
        all_field_names = [rule["field"] for rule in rules]
        uniq_field_names = list(set(all_field_names))
        assert len(list(rules)) == len(
            uniq_field_names
        ), f"must only have 1 function per field. fields passed: {str(sorted(all_field_names))}"
        for field in uniq_field_names:
            SeratoBinDb._check_valid_field(field)
