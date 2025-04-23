import mutagen.id3
from mutagen.id3._frames import GEOB
from mutagen.mp3 import MP3

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
    if key in tagfile:
        del tagfile[key]


def del_geob(tagfile: _MutagenTagFile, geob_key: str):
    del_tag(tagfile, f"GEOB:{geob_key}")
