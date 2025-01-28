import mutagen


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

def get_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str) -> bytes:
    geob_key = f"GEOB:{geob_key}"
    try:
        return tagfile[geob_key].data
    except KeyError:
        raise KeyError(f'File is missing "{geob_key}" tag')

def tag_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str, data: bytes):
    tagfile[f"GEOB:{geob_key}"] = mutagen.id3.GEOB(
        encoding=0,
        mime='application/octet-stream',
        desc=geob_key,
        data=data,
    )

def del_geob(tagfile: mutagen.id3.ID3FileType, geob_key: str):
    geob_key = f"GEOB:{geob_key}"
    if geob_key in tagfile:
        del tagfile[geob_key]