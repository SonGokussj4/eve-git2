import utils
import pytest
from io import StringIO


def test_ask_with_defaults_true(monkeypatch):
    # monkeypatch.setattr('sys.stdin', StringIO('\n'.join(('first', 'second', ' '))))
    monkeypatch.setattr('sys.stdin', StringIO('yes\n'))
    assert utils.ask_with_defaults('Are you first?') == 'yes'

    monkeypatch.setattr('sys.stdin', StringIO('yes\n'))
    assert utils.ask_with_defaults('Are you second?', defaults='no') == 'yes'

    monkeypatch.setattr('sys.stdin', StringIO('\n'))
    assert utils.ask_with_defaults('Are you second?', defaults='no') == 'no'

    monkeypatch.setattr('sys.stdin', StringIO('Suzumiya Haruhi\n'))
    assert utils.ask_with_defaults('Best movie?', defaults='Sex in the city') != 'Silence of the labs'


@pytest.mark.parametrize(
    "question, defaults, user_input, result", [
        ('Are you first?', '', 'yes\n', 'yes'),
        ('Are you second?', 'no', 'yes\n', 'yes'),
        ('Are you second?', 'no', '\n', 'no'),
        ('Are you first?', 'Sex in the city', 'Suzumiya Haruhi\n', '!Silence of the lambs'),
    ])
def test_ask_with_defaults(monkeypatch, question, defaults, user_input, result):
    monkeypatch.setattr('sys.stdin', StringIO(user_input))
    if result.startswith('!'):
        result = result[1:]
        assert utils.ask_with_defaults(question, defaults) != result
    else:
        assert utils.ask_with_defaults(question, defaults) == result
