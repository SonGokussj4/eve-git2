# from eve_git import create_repo
import pytest
from io import StringIO
# import utils


class TestClass:
    def test_one(self):
        x = "this"
        assert "h" in x

    # def test_two(self):
    #     x = "hello"
    #     assert hasattr(x, "check")


def secti(x, y):
    return x + y


def zeptej_secti():
    x = input("First: ")
    y = input("Second: ")
    z = int(x) + int(y)
    return z


def test_secti():
    assert secti(1, 1) == 2
    assert secti(1, 2) == 3
    assert secti(0, 0) == 0


@pytest.mark.parametrize("prvni, druhy, vysledek", [
    (1, 2, 3),
    (50, 0, 50),
    # (20, 0, 10),
])
def test_secti2(prvni, druhy, vysledek):
    assert secti(prvni, druhy) == vysledek


def test_zeptej_secti(monkeypatch):
    monkeypatch.setattr('sys.stdin', StringIO('1\n2'))
    assert zeptej_secti() == 3

    monkeypatch.setattr('sys.stdin', StringIO('0\n-5'))
    assert zeptej_secti() == -5


@pytest.mark.parametrize("args, vysledek", [
    ('1\n2', 3),
    ('25\n25', 50),
])
def test_zeptej_secti2(monkeypatch, args, vysledek):
    monkeypatch.setattr('sys.stdin', StringIO(args))
    assert zeptej_secti() == vysledek
