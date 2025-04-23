__Includes:__

- Serato track file tag parsing and modification, including cue points, beatgrid, waveform (from https://github.com/Holzhaus/serato-tags , which appears to be no longer maintained)
- Serato library database parsing and modification
- Serato crate parsing and modification (from https://github.com/sharst/seratopy)
- Dynamic beatgrid analysis (from [https://github.com/heyitsmass/audio](https://github.com/heyitsmass/audio/blob/master/audio/beat_grid.py)) that can be saved to a track file. Rekordbox has this but Serato doesn't. This analyzes a non-consistent BPM across a track, such as a track with live drums, and snaps a beatgrid marker to each beat. Have only tested this on a few tracks, and requires some review on the generated grid markers in Serato-- but it seems to work pretty great!

# Installation

```cmd
pip install serato-tools
```
The following deps are optional, but __must be installed based on what features you want to use__:

- For getting/modifying track metadata including tags, cue points, beagrid, and waveform, must install `pip install mutagen`
- For viewing a track's waveform, must install `pip install pillow`
- For beatgrid analysis, must install `pip install numpy` and `pip install librosa`

# Examples

### Analyzing and setting a dynamic beatgrid

_NOTE: This feature has only been tested on a couple of tracks. Reccomend reviewing the resulting beatgrid in Serato— some grid markers may require adjustment._

```cmd
>>> analyze_beatgrid "Music/Dubstep/Mind Splitter - YAPPIN'.mp3"
```

### Modifying the database file

_NOTE: Reccomended to make a backup of the database file elsewhere, before modifying via this package, in case an unforseen bug appears._

```python
from serato_tools.database_v2 import DatabaseV2

db = DatabaseV2()

now = int(time.time())

def modify_uadd(filename: str, prev_val: Any):
    print(f'Serato library change - Changed "date added" to today: {filename}')
    return now

def modify_tadd(filename: str, prev_val: Any):
    return str(now)

def remove_group(filename: str, prev_val: Any):
    return " "

# a list of field keys can be found in serato_tools.database_v2
db.modify_file(
    rules=[
        {"field": "uadd", "files": files_set_date, "func": modify_uadd},
        {"field": "tadd", "files": files_set_date, "func": modify_tadd},
        {"field": "tgrp", "func": remove_group}, # all files
    ]
)
```

### Setting track color

```python
from serato_tools.track_cues_v2 import TRACK_COLORS, set_track_color

set_track_color('/Users/Username/Music/Dubstep/Raaket - ILL.mp3',
    TRACK_COLORS["purple"],
    print_changes=True,
    delete_tags_v1=True
    # Must delete delete_tags_v1 in order for track color change to appear in Serato (since we never change tags_v1 along with it (TODO)). Not sure what tags_v1 is even for, probably older versions of Serato. Have found no issues with deleting this, but use with caution if running an older version of Serato.
)

```

### Modifying track metadata / hot cues

```python
from mutagen.mp3 import MP3
from mutagen.id3._frames import TIT1

from serato_tools.track_cues_v2 import CUE_COLORS, TRACK_COLORS, ValueType, modify_file_entries
from serato_tools.utils.track_tags import del_geob

tagfile = MP3(file)

def red_fix(prev_val: ValueType):
    if prev_val in [CUE_COLORS["pinkred"], CUE_COLORS["magenta"]]:
        print("Cue close to red, changed to red")
        return CUE_COLORS["red"]

def name_changes(prev_val: ValueType):
    if (not isinstance(prev_val, str)) or prev_val == "":
        return

    # make cue names all caps
    val_caps = prev_val.strip().upper()
    if prev_val != val_caps:
        return val_caps

def set_grouping_based_on_track_color(prev_val: ValueType):
    if prev_val == TRACK_COLORS["limegreen3"]:
        tagfile.tags.setall("TIT1", [TIT1(text="TAGGED")])
    elif prev_val in [ TRACK_COLORS["white"], TRACK_COLORS["grey"], TRACK_COLORS["black"]]:
        tagfile.tags.setall("TIT1", [TIT1(text="UNTAGGED")])

modify_file_entries(
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
    print_changes=True,
    delete_tags_v1=True
    # Must delete delete_tags_v1 in order for many tags_v2 changes appear in Serato (since we never change tags_v1 along with it (TODO)). Not sure what tags_v1 is even for, probably older versions of Serato. Have found no issues with deleting this, but use with caution if running an older version of Serato.
)
```

### Crate details and adding a track

```python
from serato_tools.crate import Crate

crate = Crate('/Users/Username/Music/_Serato_/Subcrates/Dubstep.crate')

print(crate)
# OUTPUT:
#
# Crate containing 81 tracks:
# Music/Dubstep/Saka - backitup.mp3
# Music/Dubstep/Mind Splitter - YAPPIN'.mp3
# Music/Dubstep/Flozone - DO IT.mp3
# Music/Dubstep/Evalution - Throw It Back.mp3
# ...

crate.print_data()
# OUTPUT:
#
# [   ('vrsn', '1.0/Serato ScratchLive Crate'),
#     ('osrt', [('brev', b'\x00')]),
#     ('ovct', [('tvcn', 'key'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'artist'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'song'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'bpm'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'playCount'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'length'), ('tvcw', '0')]),
#     ('ovct', [('tvcn', 'added'), ('tvcw', '0')]),
#     (   'otrk',
#         [   (   'ptrk',
#                 'Music/Dubstep/Flozone - Candy Paint')]),
#     (   'otrk',
#         [   (   'ptrk',
#                 'Music/Dubstep/Mind Splitter - LISTEN TO ME')]),
#     ('otrk', [('ptrk', 'Music/Dubstep/Flozone - DO IT')]),
# ...


# Example: Add a track to the crate and save it as a new crate
crate.add_track('/Users/Username/Music/Dubstep/Chozen - I Wanna Dance.mp3')
crate.save_to_file('/Users/Username/Music/Dubstep/New Crate.crate')
```

# Serato Tags

Original writeup on Serato GEOB tag discoveries: [blog post](https://homepage.ruhr-uni-bochum.de/jan.holthuis/posts/reversing-seratos-geob-tags)

| GEOB Tag                                     | Research Progress | Contents                                                                        | Script File                                  |
| -------------------------------------------- | ----------------- | ------------------------------------------------------------------------------- | -------------------------------------------- |
| [`Serato Analysis`](docs/serato_analysis.md) | Done              | Serato version information                                                      |
| [`Serato Autotags`](docs/serato_autotags.md) | Done              | BPM and Gain values                                                             | [`track_autotags.py`](src/track_autotags.py) |
| [`Serato BeatGrid`](docs/serato_beatgrid.md) | Mostly done       | Beatgrid Markers                                                                | [`track_beatgrid.py`](src/track_beatgrid.py) |
| [`Serato Markers2`](docs/serato_markers2.md) | Mostly done       | Hotcues, Saved Loops, etc.<br>_(The main one used in newer versions of Serato)_ | [`track_cues_v2.py`](src/track_cues_v2.py)   |
| [`Serato Markers_`](docs/serato_markers_.md) | Mostly done       | Hotcues, Saved Loops, etc.<br>_(Old, not used in newer versions of Serato)_     | [`track_cues_v1.py`](src/track_cues_v1.py)   |
| [`Serato Offsets_`](docs/serato_offsets_.md) | _Not started_     | ???                                                                             |
| [`Serato Overview`](docs/serato_overview.md) | Done              | Waveform data                                                                   | [`track_waveform.py`](src/track_waveform.py) |

The different file/tag formats that Serato uses to store the information are documented in [`docs/fileformats.md`](docs/fileformats.md), a script to dump the tag data can be found at [`track_tagdump.py`](src/track_tagdump.py).

# Contributing

If you want a new feature, or have a bug fix, please put in a PR!