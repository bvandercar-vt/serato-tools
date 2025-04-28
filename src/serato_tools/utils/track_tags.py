import io
import struct

import mutagen.id3
from mutagen.id3._frames import GEOB

_MutagenTagFile = mutagen.id3.ID3FileType | mutagen.id3.ID3


def get_geob(tagfile: _MutagenTagFile, geob_key: str) -> bytes:
    geob_key = f"GEOB:{geob_key}"
    try:
        return tagfile[geob_key].data
    except KeyError:
        raise KeyError(f'File is missing "{geob_key}" tag')


def tag_geob(tagfile: _MutagenTagFile, geob_key: str, data: bytes):
    tagfile[f"GEOB:{geob_key}"] = GEOB(
        encoding=0,
        mime="application/octet-stream",
        desc=geob_key,
        data=data,
    )


def del_tag(tagfile: _MutagenTagFile, key: str):
    """
    Returns True if was deleted, False if no change
    """
    if key in tagfile:
        del tagfile[key]
        return True
    return False


def del_geob(tagfile: _MutagenTagFile, geob_key: str):
    """
    Returns True if was deleted, False if no change
    """
    return del_tag(tagfile, f"GEOB:{geob_key}")


VERSION_FORMAT = "BB"
VersionType = tuple[int, int]


def check_version(given: bytes, expected: VersionType):
    given_version = struct.unpack(VERSION_FORMAT, given)
    if given_version != expected:
        raise ValueError(
            f"Wrong version. Expected: {str(expected)} Given: {str(given_version)}"
        )


def pack_version(version: VersionType):
    return struct.pack(VERSION_FORMAT, *version)
