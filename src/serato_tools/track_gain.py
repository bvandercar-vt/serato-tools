import os
import sys
from typing import Optional

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from serato_tools.utils.track_tags import SeratoTrack


class TrackGain(SeratoTrack):
    REPLAY_GAIN_GAIN_KEY = "replaygain_SeratoGain_gain"
    REPLAY_GAIN_PEAK_KEY = "replaygain_SeratoGain_peak"

    def __init__(self, file: SeratoTrack.FileArg):
        super().__init__(file)
        self.gain: float | None = self.tagfile.get(TrackGain.REPLAY_GAIN_GAIN_KEY, None)
        self.peak: float | None = self.tagfile.get(TrackGain.REPLAY_GAIN_PEAK_KEY, None)

    def __str__(self) -> str:
        return f"gain: {self.gain}\npeak: {self.peak}"

    def set_and_save(self, gain: Optional[float] = None, peak: Optional[float] = None):
        if gain is not None:
            self.gain = gain
        if peak is not None:
            self.peak = peak

        self.tagfile[TrackGain.REPLAY_GAIN_GAIN_KEY] = self.gain
        self.tagfile[TrackGain.REPLAY_GAIN_PEAK_KEY] = self.peak
        self.tagfile.save()

    def save(self):
        self.tagfile.save()

    def delete(self):
        for key in [TrackGain.REPLAY_GAIN_GAIN_KEY, TrackGain.REPLAY_GAIN_PEAK_KEY]:
            if key in self.tagfile:
                del self.tagfile[key]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    tags = TrackGain(args.file)
    print(str(tags))
