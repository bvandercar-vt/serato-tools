import sys

REPLAY_GAIN_GAIN_KEY = "replaygain_SeratoGain_gain"
REPLAY_GAIN_PEAK_KEY = "replaygain_SeratoGain_peak"


def main(argv=None):
    import argparse

    import mutagen._file

    parser = argparse.ArgumentParser()
    parser.add_argument("file", metavar="FILE")
    args = parser.parse_args(argv)

    tagfile = mutagen._file.File(args.file)
    if tagfile is not None:
        gain = tagfile.get(REPLAY_GAIN_GAIN_KEY, None)
        peak = tagfile.get(REPLAY_GAIN_PEAK_KEY, None)
        print(f"gain: {gain}")
        print(f"peak: {peak}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
