import math
import pytest
from geometri import luas_lingkaran, keliling_lingkaran


def test_luas_lingkaran_jari_jari_1():
    assert luas_lingkaran(1) == math.pi


def test_luas_lingkaran_jari_jari_0():
    assert luas_lingkaran(0) == 0


def test_luas_lingkaran_jari_jari_5():
    assert luas_lingkaran(5) == math.pi * 25


def test_keliling_lingkaran_jari_jari_1():
    assert keliling_lingkaran(1) == 2 * math.pi


def test_keliling_lingkaran_jari_jari_0():
    assert keliling_lingkaran(0) == 0


def test_keliling_lingkaran_jari_jari_5():
    assert keliling_lingkaran(5) == 10 * math.pi
