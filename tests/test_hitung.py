import pytest
from hitung import is_prime


def test_is_prime_2():
    assert is_prime(2) == True


def test_is_prime_3():
    assert is_prime(3) == True


def test_is_prime_4():
    assert is_prime(4) == False


def test_is_prime_5():
    assert is_prime(5) == True


def test_is_prime_10():
    assert is_prime(10) == False
