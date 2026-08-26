def reverse_words(kalimat):
    """Membalik urutan kata-kata dalam kalimat."""
    kata_kata = kalimat.split()
    return ' '.join(reversed(kata_kata))


def palindrome(teks):
    """Mengecek apakah teks adalah palindrome (mengabaikan spasi dan huruf besar/kecil)."""
    teks_bersih = teks.replace(' ', '').lower()
    return teks_bersih == teks_bersih[::-1]
