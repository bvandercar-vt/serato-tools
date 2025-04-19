Includes:
- Serato file GEOB tag parsing and modification (from https://github.com/Holzhaus/serato-tags , which appears to be no longer maintained)
- Serato overall database parsing and modification
- Serato Crate parsing and modification (from https://github.com/sharst/seratopy)
- Dynamic beatgrid analysis and saving to Serato tags (beatgrid analysis from https://github.com/heyitsmass/audio/blob/master/audio/beat_grid.py)

# Serato Tags

Original writeup on Serato GEOB tag discoveries: [blog post](https://homepage.ruhr-uni-bochum.de/jan.holthuis/posts/reversing-seratos-geob-tags)

| Tag                                          | Progress      | Contents                   | Example script                               |
| -------------------------------------------- | ------------- | -------------------------- | -------------------------------------------- |
| [`Serato Analysis`](docs/serato_analysis.md) | Done          | Serato version information |
| [`Serato Autotags`](docs/serato_autotags.md) | Done          | BPM and Gain values        | [`track_autotags.py`](src/track_autotags.py) |
| [`Serato BeatGrid`](docs/serato_beatgrid.md) | Mostly done   | Beatgrid Markers           | [`track_beatgrid.py`](src/track_beatgrid.py) |
| [`Serato Markers2`](docs/serato_markers2.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`track_cues_v2.py`](src/track_cues_v2.py)   |
| [`Serato Markers_`](docs/serato_markers_.md) | Mostly done   | Hotcues, Saved Loops, etc. | [`track_cues_v1.py`](src/track_cues_v1.py)   |
| [`Serato Offsets_`](docs/serato_offsets_.md) | _Not started_ |                            |
| [`Serato Overview`](docs/serato_overview.md) | Done          | Waveform data              | [`track_waveform.py`](src/track_waveform.py) |

The different file/tag formats that Serato uses to store the information are documented in [`docs/fileformats.md`](docs/fileformats.md), a script to dump the tag data can be found at [`track_tagdump.py`](src/track_tagdump.py).

# Examples

### Analyzing and setting a dynamic beatgrid

```cmd
>>> analyze_beatgrid "Music/Techno/Adam Beyer - Space Date (Pleasurekraft Remix).mp3"
```

### Modifying the database file

```python
import serato_tools.database_v2

now = int(time.time())

def modify_uadd(filename: str, value: Any):
    print(f'Serato library change - Changed "date added" to today: {filename}')
    return now

def modify_tadd(filename: str, value: Any):
    return str(now)

def remove_group(filename: str, value: Any):
    return " "

# a list of field keys can be found in serato_tools.database_v2
serato_tools.database_v2.modify_file(
    rules=[
        {"field": "uadd", "files": files_set_date, "func": modify_uadd},
        {"field": "tadd", "files": files_set_date, "func": modify_tadd},
        {"field": "tgrp", "func": remove_group}, # all files
    ]
)
```

### Setting track color

Is Buggy, sometimes doesn't show up in Serato. TODO: debug

```python
from serato_tools.track_cues_v2 import TRACK_COLORS, set_track_color

set_track_color('/Users/Username/Music/Techno/T78 - Acid Lick.mp3', TRACK_COLORS["purple"], print_changes=True)

```

### Modifying track metadata / hot cues

```python
from mutagen.mp3 import MP3
from mutagen.id3._frames import TIT1

import serato_tools.track_cues_v1
from serato_tools.track_cues_v2 import CUE_COLORS, TRACK_COLORS, ValueType, modify_file_entries
from serato_tools.utils.tags import del_geob

tagfile = MP3(file)

def red_fix(value: ValueType):
    if value in [CUE_COLORS["pinkred"], CUE_COLORS["magenta"]]:
        print("Cue changed to red")
        del_geob(tagfile, serato_tools.track_cues_v1.GEOB_KEY) # delete serato_markers, not sure if this field even takes effect in new versions of Serato, we just want serato_markers2
        return CUE_COLORS["red"]

def name_changes(value: ValueType):
    if (not isinstance(value, str)) or value == "":
        return

    # make cue names all caps
    value_caps = value.strip().upper()
    if value != value_caps:
        return value_caps

def set_grouping_based_on_track_color(value: ValueType):
    if value == TRACK_COLORS["limegreen3"]:
        tagfile.tags.setall("TIT1", [TIT1(text="TAGGED")])
    elif value in [ TRACK_COLORS["white"], TRACK_COLORS["grey"], TRACK_COLORS["black"]]:
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
    print_changes=True
)
```

### Crate details and adding a track

```python
from serato_tools.crate import Crate

crate = Crate('/Users/Username/Music/_Serato_/Subcrates/Techno.crate')

print(crate)
# OUTPUT:
#
# Crate containing 81 tracks:
# Music/Techno/Adam Beyer - Space Date (Pleasurekraft Remix).mp3
# Music/Techno/Adam Beyer - Your Mind (Will Clarke Remix).mp3
# Music/Techno/Adam Beyer - Your Mind.mp3
# Music/Techno/Alberto Ruiz - Expressor (Hell Driver Remix).mp3
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
#                 'Music/Techno/Adam Beyer - Space Date (Pleasurekraft Remix).mp3')]),
#     (   'otrk',
#         [   (   'ptrk',
#                 'Music/Techno/Adam Beyer - Your Mind (Will Clarke Remix).mp3')]),
#     ('otrk', [('ptrk', 'Music/Techno/Adam Beyer - Your Mind.mp3')]),
# ...


# Example: Add a track to the crate and save it as a new crate
crate.add_track('/Users/Username/Music/Techno/T78 - Acid Lick.mp3')
crate.save_to_file('/Users/Username/Music/Techno/New Crate.crate')
```
