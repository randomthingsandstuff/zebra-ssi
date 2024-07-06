from ssi_barcode import util
import unittest

class TestBinaryDecoder(unittest.TestCase):

    def test_read_uint32_be(self):
        data = b'\x00\x00\x00\x10'  # represents the integer 16 in big-endian byte order
        decoder = util.BinaryDecoder(data)
        self.assertEqual(decoder.read_uint32_be(), 16)
        self.assertEqual(decoder.offset, 4)

if __name__ == '__main__':
    unittest.main()

