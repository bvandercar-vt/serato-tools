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

