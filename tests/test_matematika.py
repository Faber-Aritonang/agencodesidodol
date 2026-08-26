import pytest
from matematika import faktorial


def test_faktorial_nol():
    assert faktorial(0) == 1


def test_faktorial_satu():
    assert faktorial(1) == 1


def test_faktorial_dua():
    assert faktorial(2) == 2


def test_faktorial_lima():
    assert faktorial(5) == 120


def test_faktorial_10():
    assert faktorial(10) == 3628800


def test_faktorial_negatif():
    with pytest.raises(ValueError):
        faktorial(-1)


def test_faktorial_string():
    with pytest.raises(TypeError):
        faktorial("5")


def test_faktorial_float():
    with pytest.raises(TypeError):
        faktorial(5.0)
