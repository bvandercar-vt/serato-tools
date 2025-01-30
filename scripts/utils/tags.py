import mutagen.id3
from mutagen.id3._frames import GEOB


def get_geob(
    tagfile: mutagen.id3.ID3FileType | mutagen.id3.ID3, geob_key: str
) -> bytes:
    geob_key = f"GEOB:{geob_key}"
    try:
        return tagfile[geob_key].data
    except KeyError:
        raise KeyError(f'File is missing "{geob_key}" tag')


def tag_geob(
    tagfile: mutagen.id3.ID3FileType | mutagen.id3.ID3, geob_key: str, data: bytes
):
    tagfile[f"GEOB:{geob_key}"] = GEOB(
        encoding=0,
        mime="application/octet-stream",
        desc=geob_key,
        data=data,
    )


def del_geob(tagfile: mutagen.id3.ID3FileType | mutagen.id3.ID3, geob_key: str):
    geob_key = f"GEOB:{geob_key}"
    if geob_key in tagfile:
        del tagfile[geob_key]
