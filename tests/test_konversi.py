import pytest
from konversi import celsius_ke_fahrenheit, km_ke_mil


def test_celsius_ke_fahrenheit_0():
    assert celsius_ke_fahrenheit(0) == 32


def test_celsius_ke_fahrenheit_100():
    assert celsius_ke_fahrenheit(100) == 212


def test_celsius_ke_fahrenheit_negatif():
    assert celsius_ke_fahrenheit(-40) == -40


def test_km_ke_mil_0():
    assert km_ke_mil(0) == 0


def test_km_ke_mil_1():
    assert km_ke_mil(1) == pytest.approx(0.621371)


def test_km_ke_mil_10():
    assert km_ke_mil(10) == pytest.approx(6.21371)
