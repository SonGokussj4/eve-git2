import os
import utils
import pytest
from io import StringIO
from pathlib import Path

SCRIPTDIR = Path(__file__).resolve().parent
TEST_FILES = SCRIPTDIR / 'files'


# def test_ask_with_defaults_true(monkeypatch):
#     # monkeypatch.setattr('sys.stdin', StringIO('\n'.join(('first', 'second', ' '))))
#     monkeypatch.setattr('sys.stdin', StringIO('yes\n'))
#     assert utils.ask_with_defaults('Are you first?') == 'yes'

#     monkeypatch.setattr('sys.stdin', StringIO('yes\n'))
#     assert utils.ask_with_defaults('Are you second?', defaults='no') == 'yes'

#     monkeypatch.setattr('sys.stdin', StringIO('\n'))
#     assert utils.ask_with_defaults('Are you second?', defaults='no') == 'no'

#     monkeypatch.setattr('sys.stdin', StringIO('Suzumiya Haruhi\n'))
#     assert utils.ask_with_defaults('Best movie?', defaults='Sex in the city') != 'Silence of the labs'


# @pytest.mark.parametrize(
#     "question, defaults, user_input, result", [
#         ('Are you first?', '', 'yes\n', 'yes'),
#         ('Are you second?', 'no', 'yes\n', 'yes'),
#         ('Are you second?', 'no', '\n', 'no'),
#         ('Are you first?', 'Sex in the city', 'Suzumiya Haruhi\n', '!Silence of the lambs'),
#     ])
# def test_ask_with_defaults(monkeypatch, question, defaults, user_input, result):
#     monkeypatch.setattr('sys.stdin', StringIO(user_input))
#     if result.startswith('!'):
#         result = result[1:]
#         assert utils.ask_with_defaults(question, defaults) != result
#     else:
#         assert utils.ask_with_defaults(question, defaults) == result


def test_remove_dir_tree():
    path = '/tmp/test_removedir'
    os.system(f'mkdir {path}')
    res = utils.remove_dir_tree(path)
    assert res is True


def test_requirements_similar_same():
    assert True is utils.requirements_similar(
        TEST_FILES / 'requirements_SRC.txt', TEST_FILES / 'requirements_SRC.txt')


def test_requirements_similar__same_req_as_string():
    assert True is utils.requirements_similar(
        str(TEST_FILES / 'requirements_SRC.txt'), str(TEST_FILES / 'requirements_SRC.txt'))


def test_requirements_similar_not_same():
    assert False is utils.requirements_similar(
        TEST_FILES / 'requirements_SRC.txt', TEST_FILES / 'requirements_DST.txt')


def test_requirements_similar_src_missing():
    assert False is utils.requirements_similar(
        TEST_FILES / 'not_a_file', TEST_FILES / 'requirements_DST.txt')


@pytest.mark.custom
def test_requirements_similar_dst_missing():
    assert False is utils.requirements_similar(
        TEST_FILES / 'requirements_SRC.txt', TEST_FILES / 'not_a_file')
