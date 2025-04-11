Fork of https://github.com/Holzhaus/serato-tags , which appears to be no longer maintained. Many updates added, including overall library tools.

# Serato Tags

Original writeup on Serato GEOB tag discoveries: [blog post](https://homepage.ruhr-uni-bochum.de/jan.holthuis/posts/reversing-seratos-geob-tags)

| Tag                                          | Progress      | Contents                   | Example script                                     |
| -------------------------------------------- | ------------- | -------------------------- | -------------------------------------------------- |
| [`Serato Analysis`](docs/serato_analysis.md) | Done          | Serato version information |
| [`Serato Autotags`](docs/serato_autotags.md) | Done          | BPM and Gain values        | [`track_autotags.py`](src/track/track_autotags.py) |
| [`Serato BeatGrid`](docs/serato_beatgrid.md) | Mostly done   | Beatgrid Markers           | [`track_beatgrid.py`](src/track/track_beatgrid.py) |
| [`Serato Markers2`](docs/serato_markers2.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`track_cues_v2.py`](src/track/track_cues_v2.py)   |
| [`Serato Markers_`](docs/serato_markers_.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`track_cues_v1.py`](src/track/track_cues_v1.py)   |
| [`Serato Offsets_`](docs/serato_offsets_.md) | _Not started_ |                            |
| [`Serato Overview`](docs/serato_overview.md) | Done          | Waveform data              | [`track_waveform.py`](src/track/track_waveform.py) |

The different file/tag formats that Serato uses to store the information are documented in [`docs/fileformats.md`](docs/fileformats.md), a script to dump the tag data can be found at [`track_tagdump.py`](src/track/track_tagdump.py).

# Examples

### Modifying the database file

```python
import serato_tools.database.database_v2

now = int(time.time())

def modify_uadd(filename: str, value: Any):
    print(f'Serato library change - Changed "date added" to today: {filename}')
    return now

def modify_tadd(filename: str, value: Any):
    return str(now)

def remove_group(filename: str, value: Any):
    return " "

# a list of field keys can be found in serato_tools.database_v2
serato_tools.database.database_v2.modify_file(
    rules=[
        {"field": "uadd", "files": files_set_date, "func": modify_uadd},
        {"field": "tadd", "files": files_set_date, "func": modify_tadd},
        {"field": "tgrp", "func": remove_group}, # all files
    ]
)
```

### Modifying track metadata / hot cues

```python
from mutagen.mp3 import MP3
from mutagen.id3._frames import TIT1

import serato_tools.tracks.track_cues_v1
from serato_tools.tracks.track_cues_v2 import CUE_COLORS, TRACK_COLORS, ValueType
from serato_tools.utils.tags import del_geob

tagfile = MP3(file)

def red_fix(value: ValueType):
    if value in [CUE_COLORS["pinkred"], CUE_COLORS["magenta"]]:
        print("Cue changed to red")
        del_geob(tagfile, serato_tools.tracks.track_cues_v1.GEOB_KEY) # delete serato_markers, not sure if this field even takes effect in new versions of Serato, we just want serato_markers2
        return CUE_COLORS["red"]

def name_changes(value: ValueType):
    if (not isinstance(value, str)) or value == "":
        return

    # remove "Energy" tag from MixedInKey
    if "Energy" in value:
        return ""

    # make cue names all caps
    value_caps = value.strip().upper()
    if value != value_caps:
        return value_caps

def set_grouping_based_on_track_color(value: ValueType):
    if value == TRACK_COLORS["limegreen3"]:
        tagfile.tags.setall("TIT1", [TIT1(text="TAGGED")])
    elif value in [ TRACK_COLORS["white"], TRACK_COLORS["grey"], TRACK_COLORS["black"]]:
        tagfile.tags.setall("TIT1", [TIT1(text="UNTAGGED")])

modify_cues(
    tagfile,
    {
        "cues": [
            {"field": "color", "func": red_fix},
            {"field": "name", "func": name_changes},
        ],
        "color": [
            {"field": "color", "func": set_grouping_based_on_track_color},
        ],
    },
)
```
