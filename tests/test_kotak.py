import kotak

import unittest

class TestKotak(unittest.TestCase):
    def test_luas_persegi(self):
        self.assertEqual(kotak.luas_persegi(1), 1)
        self.assertEqual(kotak.luas_persegi(2), 4)
        self.assertEqual(kotak.luas_persegi(3), 9)

if __name__ == '__main__':
    unittest.main()