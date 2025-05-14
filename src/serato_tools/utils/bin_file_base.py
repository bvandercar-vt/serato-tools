import os
from typing import Iterable, TypedDict
from enum import StrEnum


class SeratoBinFile:
    FIELDNAME_MAP = {
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
        # Smart Crates
        "rurt": "SmartCrate Rule",
        "rlut": "SmartCrate Live Update",
        "rart": "SmartCrate Match All",
        "trpt": "Rule Value Text",
        "trtt": "Rule Value Date",
        "urpt": "Rule Value Integer",
        "trft": "Rule Comparison",
        "urkt": "Rule Field",
    }
    FIELDNAMES = list(FIELDNAME_MAP.keys())

    class Fields(StrEnum):
        TRACK = "otrk"
        FILE = "pfil"

    raw_data: bytes

    def __repr__(self):
        return str(self.raw_data)

    @staticmethod
    def get_field_name(field: str):
        return SeratoBinFile.FIELDNAME_MAP.get(field, "Unknown Field")

    @staticmethod
    def _get_type(field: str) -> str:
        # vrsn field has no type_id, but contains text ("t")
        return "t" if field == "vrsn" else field[0]

    @staticmethod
    def _check_valid_field(field: str):
        if field not in SeratoBinFile.FIELDNAMES:
            raise ValueError(
                f"invalid field: {field} must be one of: {str(SeratoBinFile.FIELDNAMES)}\n(see {__file__} for what these keys map to)"
            )

    @staticmethod
    def format_filepath(filepath: str) -> str:
        drive, filepath = os.path.splitdrive(filepath)  # pylint: disable=unused-variable
        return os.path.normpath(filepath).replace(os.path.sep, "/").lstrip("/")

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
            SeratoBinFile._check_valid_field(field)
