import struct
import logging
import io

from mutagen.mp3 import MP3
from mutagen.aiff import AIFF
from mutagen.id3._frames import GEOB


class SeratoTrack:
    TagfileType = MP3 | AIFF
    FileArgType = str | TagfileType

    def __init__(self, file: FileArgType):
        self.tagfile: SeratoTrack.TagfileType
        if isinstance(file, str):
            try:
                self.tagfile = MP3(file)
            except:
                logging.error("Mutagen error for file %s" % file)
                raise
        else:
            self.tagfile = file

    def _get_geob(self, geob_key: str) -> bytes | None:
        geob_key = f"GEOB:{geob_key}"
        try:
            return self.tagfile[geob_key].data
        except KeyError:
            logging.debug(
                f'File is missing "{geob_key}" tag, not yet set',
                self.tagfile.filename,
            )
            return None

    def _tag_geob(self, geob_key: str, data: bytes):
        self.tagfile[f"GEOB:{geob_key}"] = GEOB(
            encoding=0,
            mime="application/octet-stream",
            desc=geob_key,
            data=data,
        )

    def _del_tag(self, key: str):
        """
        Returns True if was deleted, False if no change
        """
        if key in self.tagfile:
            del self.tagfile[key]
            return True
        return False

    def _del_geob(self, geob_key: str):
        """
        Returns True if was deleted, False if no change
        """
        return self._del_tag(f"GEOB:{geob_key}")

    VERSION_FORMAT = "BB"
    VERSION_LEN = struct.calcsize(VERSION_FORMAT)
    VersionType = tuple[int, int]

    @staticmethod
    def _check_version(given: bytes, expected: VersionType):
        given_version = struct.unpack(SeratoTrack.VERSION_FORMAT, given)
        if given_version != expected:
            raise ValueError(
                f"Wrong version. Expected: {str(expected)} Given: {str(given_version)}"
            )

    @staticmethod
    def _pack_version(version: VersionType):
        return struct.pack(SeratoTrack.VERSION_FORMAT, *version)

    @staticmethod
    def _readbytes(fp: io.BytesIO):
        for x in iter(lambda: fp.read(1), b""):
            if x == b"\00":
                break
            yield x


class SeratoTag(SeratoTrack):
    GEOB_KEY: str
    VERSION: tuple[int, int]

    FileOrDataType = SeratoTrack.FileArgType | bytes

    def __init__(self, file_or_data: FileOrDataType):
        self.tagfile: SeratoTrack.TagfileType | None = None
        self.raw_data: bytes | None = None

        if isinstance(file_or_data, (bytes, bytearray, memoryview)):
            self.raw_data = file_or_data
        else:
            super().__init__(file=file_or_data)
            self.raw_data = self._get_geob()

    def __repr__(self):
        return str(self.raw_data)

    def _get_geob(self):
        return super()._get_geob(self.GEOB_KEY)

    def _tag_geob(self):
        if self.raw_data is None:
            return
        return super()._tag_geob(self.GEOB_KEY, self.raw_data)

    def _del_geob(self):
        return super()._del_geob(self.GEOB_KEY)

    def _check_version(self, given: bytes):
        return super()._check_version(given, self.VERSION)

    def _pack_version(self):
        return super()._pack_version(self.VERSION)

    def delete(self):
        return self._del_geob()

    def save(self):
        if not self.tagfile:
            raise Exception("no tagfile, no saving")
        if self.raw_data is None:
            raise ValueError("no data to save")
        self._tag_geob()
        self.tagfile.save()
