import utils
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
