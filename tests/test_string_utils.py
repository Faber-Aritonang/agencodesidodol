import pytest
from string_utils import reverse_words, palindrome


class TestReverseWords:
    def test_satu_kata(self):
        assert reverse_words("halo") == "halo"

    def test_dua_kata(self):
        assert reverse_words("halo dunia") == "dunia halo"

    def test_tiga_kata(self):
        assert reverse_words("saya suka python") == "python suka saya"

    def test_kalimat_kosong(self):
        assert reverse_words("") == ""

    def test_spasi_ganda(self):
        assert reverse_words("  halo   dunia  ") == "dunia halo"


class TestPalindrome:
    def test_palindrome_sederhana(self):
        assert palindrome("katak") is True

    def test_palindrome_singkat(self):
        assert palindrome("gag") is True

    def test_palindrome_kalimat(self):
        assert palindrome("A man a plan a canal Panama") is True

    def test_bukan_palindrome(self):
        assert palindrome("halo") is False

    def test_kosong(self):
        assert palindrome("") is True

    def test_satu_karakter(self):
        assert palindrome("a") is True
