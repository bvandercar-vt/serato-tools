import os
import shutil

import mutagen.id3
from mutagen.id3._frames import GEOB


def ui_ask(question, choices, default=None):
    text = '{question} [{choices}]? '.format(
        question=question,
        choices='/'.join(
            x.upper() if x == default else x
            for x in (*choices.keys(), '?')
        )
    )

    while True:
        answer = input(text).lower()
        if default and answer == '':
            answer = default

        if answer in choices.keys():
            return answer
        else:
            print('\n'.join(
                '{} - {}'.format(choice, desc)
                for choice, desc in (*choices.items(), ('?', 'print help'))
            ))

def get_text_editor():
    text_editor = shutil.which(os.getenv('EDITOR', 'vi'))
    if not text_editor:
        raise Exception('No suitable EDITOR found.')
    return text_editor

def get_hex_editor():
    hex_editor = shutil.which(os.getenv('HEXEDITOR', 'bvi'))
    if not hex_editor:
        raise Exception('No suitable HEXEDITOR found.')
    return hex_editor

def get_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str) -> bytes:
    geob_key = f"GEOB:{geob_key}"
    try:
        return tagfile[geob_key].data
    except KeyError:
        raise KeyError(f'File is missing "{geob_key}" tag')

def tag_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str, data: bytes):
    tagfile[f"GEOB:{geob_key}"] = GEOB(
        encoding=0,
        mime='application/octet-stream',
        desc=geob_key,
        data=data,
    )

def del_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str):
    geob_key = f"GEOB:{geob_key}"
    if geob_key in tagfile:
        del tagfile[geob_key]