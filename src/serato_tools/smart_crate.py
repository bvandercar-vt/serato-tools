import os
import sys
from typing import cast
from enum import StrEnum, IntEnum

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.crate_base import CrateBase
from serato_tools.utils import get_enum_key_from_value, parse_cli_keys_and_values, SERATO_DIR, DataTypeError


class SmartCrate(CrateBase):
    EXTENSION = ".scrate"
    DIR = "SmartCrates"
    DIR_PATH = os.path.join(SERATO_DIR, DIR)

    class RuleField(IntEnum):
        ADDED = 25
        ALBUM = 8
        ARTIST = 7
        BPM = 15
        COMMENT = 17
        COMPOSER = 22
        FILENAME = 4
        GENRE = 9
        GROUPING = 19
        KEY = 51
        LABEL = 21
        PLAYS = 79
        REMIXER = 20
        SONG = 6
        YEAR = 23

    class RuleComparison(StrEnum):
        STR_CONTAINS = "cond_con_str"
        STR_DOES_NOT_CONTAIN = "cond_dnc_str"
        STR_IS = "cond_is_str"
        STR_IS_NOT = "cond_isn_str"
        STR_DATE_BEFORE = "cond_bef_str"
        STR_DATE_AFTER = "cond_aft_str"
        TIME_IS_BEFORE = "cond_bef_time"
        TIME_IS_AFTER = "cond_aft_time"
        INT_IS_GE = "cond_greq_uint"
        INT_IS_LE = "cond_lseq_uint"

    DEFAULT_DATA = [
        (CrateBase.Fields.VERSION, "1.0/Serato ScratchLive Smart Crate"),
        (CrateBase.Fields.SMARTCRATE_MATCH_ALL, [("brut", False)]),
        (CrateBase.Fields.SMARTCRATE_LIVE_UPDATE, [("brut", False)]),
        (CrateBase.Fields.SORTING, [(CrateBase.Fields.COLUMN_NAME, "key"), (CrateBase.Fields.REVERSE_ORDER, False)]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "song"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "playCount"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "artist"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "bpm"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "key"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "album"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "length"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "comment"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
        (CrateBase.Fields.COLUMN, [(CrateBase.Fields.COLUMN_NAME, "added"), (CrateBase.Fields.COLUMN_WIDTH, "0")]),
    ]

    @staticmethod
    def _get_rule_field_from_val(value: int) -> str:
        return get_enum_key_from_value(value, SmartCrate.RuleField)

    @staticmethod
    def _get_rule_comparison_from_val(value: str) -> str:
        return get_enum_key_from_value(value, SmartCrate.RuleComparison)

    @staticmethod
    def _get_rule_field_from_key(key: str):
        try:
            return SmartCrate.RuleField[key.upper()]
        except KeyError as exc:
            raise KeyError(
                f"bad field {key.upper()} , must be one of {[c.name for c in SmartCrate.RuleField]}"
            ) from exc

    @staticmethod
    def _get_rule_comparison_from_key(key: str):
        try:
            return SmartCrate.RuleComparison[key.upper()]
        except KeyError as exc:
            raise KeyError(
                f"bad comparison {key.upper()} , must be one of {[c.name for c in SmartCrate.RuleComparison]}"
            ) from exc

    @staticmethod
    def _get_rule_value_type(value: str | int):
        if isinstance(value, int):
            return SmartCrate.Fields.RULE_VALUE_INTEGER
        elif isinstance(value, str):
            return SmartCrate.Fields.RULE_VALUE_TEXT
        else:
            raise TypeError(f"Bad type: {type(value)} (value: {value})")

    def _stringify_value(self, entry: CrateBase.Entry, indent: int = 0) -> str:
        field, fieldname, value = entry  # pylint: disable=unused-variable
        if isinstance(value, list):
            return self._stringify_entries(value, indent)

        ret_val = str(value)
        if field == CrateBase.Fields.RULE_FIELD:
            if not isinstance(value, int):
                raise DataTypeError(value, int, field)
            ret_val += f" ({self._get_rule_field_from_val(value).lower()})"
        elif field == CrateBase.Fields.RULE_COMPARISON:
            if not isinstance(value, str):
                raise DataTypeError(value, str, field)
            ret_val += f" ({self._get_rule_comparison_from_val(value)})"

        return ret_val

    class Rule(CrateBase.StructCls):
        def __init__(self, data: "CrateBase.Struct"):
            super().__init__(data)

            # TODO: check and ensure types

            self.comparison = self.get_value(SmartCrate.Fields.RULE_COMPARISON)
            self.field = self.get_value(SmartCrate.Fields.RULE_FIELD)

            def try_to_get_value(field: str):
                try:
                    return self.get_value(field)
                except AttributeError:
                    return None

            self.value = cast(
                str | int | float,  # float for date or no?
                (
                    try_to_get_value(SmartCrate.Fields.RULE_VALUE_INTEGER)
                    or try_to_get_value(SmartCrate.Fields.RULE_VALUE_TEXT)
                    or try_to_get_value(SmartCrate.Fields.RULE_VALUE_DATE)
                ),
            )

        def set_value(self, value: str | int):  # pyright: ignore[reportIncompatibleMethodOverride]
            field = SmartCrate._get_rule_value_type(value)  # pylint: disable=protected-access
            super().set_value(field, value)

        def set_field(self, value: "SmartCrate.RuleField"):
            super().set_value(SmartCrate.Fields.RULE_FIELD, value.value)

        def set_comparison(self, value: "SmartCrate.RuleComparison"):
            super().set_value(SmartCrate.Fields.RULE_COMPARISON, value.value)

    def set_rule(self, field: "SmartCrate.RuleField", comparison: "SmartCrate.RuleComparison", value: str | int):
        rule_field_id = field.value
        rule_exists: bool = False
        new_data: SmartCrate.Struct = []
        for f, v in self.data:  # pylint: disable=access-member-before-definition
            if f == CrateBase.Fields.SMARTCRATE_RULE:
                if not isinstance(v, list):
                    raise DataTypeError(v, list, f)
                rule = SmartCrate.Rule(v)
                if rule.field == rule_field_id:
                    rule.set_value(value)
                    rule.set_comparison(comparison)
                    rule_exists = True
                v = rule.to_struct()
            new_data.append((f, v))

        if not rule_exists:
            new_rule = SmartCrate.Rule(
                [
                    (SmartCrate.Fields.RULE_COMPARISON.value, comparison.value),
                    (SmartCrate.Fields.RULE_FIELD.value, rule_field_id),
                    (SmartCrate._get_rule_value_type(value).value, value),
                ]
            )
            new_data.append((CrateBase.Fields.SMARTCRATE_RULE.value, new_rule.to_struct()))

        self.data = new_data  # pylint: disable=attribute-defined-outside-init
        self._dump()

    def delete_rule(self, field: "SmartCrate.RuleField"):
        rule_field_id = field.value
        new_data: SmartCrate.Struct = []
        for f, v in self.data:  # pylint: disable=access-member-before-definition
            if f == CrateBase.Fields.SMARTCRATE_RULE:
                if not isinstance(v, list):
                    raise DataTypeError(v, list, f)
                rule = SmartCrate.Rule(v)
                if rule.field == rule_field_id:
                    continue
            new_data.append((f, v))

        self.data = new_data  # pylint: disable=attribute-defined-outside-init
        self._dump()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file_or_dir", nargs="?", help="Set the crate file, or a directory to do all files in it")
    parser.add_argument("--all", action="store_true", help="Perform actions on all crates.")
    parser.add_argument("-l", "--list_tracks", action="store_true", help="Only list tracks")
    parser.add_argument("-f", "--filenames_only", action="store_true", help="Only list track filenames")
    parser.add_argument(
        "--set_rules",
        nargs=argparse.REMAINDER,
        help="Set rules for all crates using key-value pairs like --grouping str_contains NEW --title str_does_not_contain NEW_TITLE\nCan also do --key DELETE",
    )
    args = parser.parse_args()

    if args.all:
        args.file_or_dir = SmartCrate.DIR_PATH

    if not args.file_or_dir:
        print(f"must pass a file or dir, or --all!\nfiles in {SmartCrate.DIR_PATH}:")
        SmartCrate.list_dir()
        sys.exit()

    paths: list[str] = (
        [os.path.join(args.file_or_dir, p) for p in os.listdir(args.file_or_dir)]
        if os.path.isdir(args.file_or_dir)
        else [args.file_or_dir]
    )

    set_rules = parse_cli_keys_and_values(args.set_rules) if args.set_rules else {}

    for p in paths:
        crate = SmartCrate(p)

        if args.set_rules:
            for key, value in set_rules.items():
                field = SmartCrate._get_rule_field_from_key(key)  # pylint: disable=protected-access
                if str(value[0]).upper() == "DELETE":
                    crate.delete_rule(field)
                else:
                    assert len(value) == 2, "must specify 2 values: a comparison and a value"
                    comparison = SmartCrate._get_rule_comparison_from_key(  # pylint: disable=protected-access
                        str(value[0])
                    )
                    crate.set_rule(field, comparison, value[1])
            crate.save()
            continue

        if args.list_tracks or args.filenames_only:
            tracks = crate.get_track_paths()
            if args.filenames_only:
                tracks = [os.path.splitext(os.path.basename(t))[0] for t in tracks]
            print("\n".join(tracks))
        else:
            print(crate)


if __name__ == "__main__":
    main()
