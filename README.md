Fork of https://github.com/Holzhaus/serato-tags , which appears to be no longer maintained. Many updates added, including overall library tools.

# Serato Tags

This repository aims to document the GEOB ID3 tags that the Serato DJ software uses to store its metadata.
You can also have a look at [this lengthy blog post](https://homepage.ruhr-uni-bochum.de/jan.holthuis/posts/reversing-seratos-geob-tags) that goes into detail how I reversed the contents of the `Serato Markers2` GEOB tag.

| Tag                                          | Progress      | Contents                   | Example script
| -------------------------------------------- | ------------- | -------------------------- | --------------
| [`Serato Analysis`](docs/serato_analysis.md) | Done          | Serato version information |
| [`Serato Autotags`](docs/serato_autotags.md) | Done          | BPM and Gain values        | [`serato_autotags.py`](scripts/serato_autotags.py)
| [`Serato BeatGrid`](docs/serato_beatgrid.md) | Mostly done   | Beatgrid Markers           | [`serato_beatgrid.py`](scripts/serato_beatgrid.py)
| [`Serato Markers2`](docs/serato_markers2.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`serato_markers2.py`](scripts/serato_markers2.py)
| [`Serato Markers_`](docs/serato_markers_.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`serato_markers_.py`](scripts/serato_markers_.py)
| [`Serato Offsets_`](docs/serato_offsets_.md) | *Not started* |                            |
| [`Serato Overview`](docs/serato_overview.md) | Done          | Waveform data              | [`serato_overview.py`](scripts/serato_overview.py)

The different file/tag formats that Serato uses to store the information are documented in [`docs/fileformats.md`](docs/fileformats.md), a script to dump the tag data can be found at [`scripts/tagdump.py`](scripts/tagdump.py).
