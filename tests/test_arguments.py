# from eve_git import create_repo
import pytest

class TestClass:
    def test_one(self):
        x = "this"
        assert "h" in x

    # def test_two(self):
    #     x = "hello"
    #     assert hasattr(x, "check")


def secti(x, y):
    return x + y


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
