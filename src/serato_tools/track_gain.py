import os
import sys

if __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

REPLAY_GAIN_GAIN_KEY = "replaygain_SeratoGain_gain"
REPLAY_GAIN_PEAK_KEY = "replaygain_SeratoGain_peak"


if __name__ == "__main__":
    import argparse

    import mutagen._file

    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    tagfile = mutagen._file.File(args.file)
    if tagfile is not None:
        gain = tagfile.get(REPLAY_GAIN_GAIN_KEY, None)
        peak = tagfile.get(REPLAY_GAIN_PEAK_KEY, None)
        print(f"gain: {gain}")
        print(f"peak: {peak}")
