import unittest
from src.cram2binxel_md import convert_cram, inspect_cram


class CramConversionTests(unittest.TestCase):
    def test_detect_uploaded_128_byte_file_as_four_rows(self):
        info = inspect_cram(bytes(128))
        self.assertEqual((info['colors'], info['total_lines']), (64, 4))

    def test_each_selected_row_exports_16_colors(self):
        data = bytes(range(128))
        for row in range(4):
            with self.subTest(row=row):
                self.assertEqual(len(convert_cram(data, selected_line=row)), 48)

    def test_all_rows_equals_concatenated_selected_rows(self):
        data = bytes(range(128))
        expected = b''.join(convert_cram(data, selected_line=row) for row in range(4))
        self.assertEqual(convert_cram(data, export_mode='all'), expected)

    def test_more_than_four_rows(self):
        data = bytes(range(7 * 32))
        info = inspect_cram(data)
        self.assertEqual(info['total_lines'], 7)
        self.assertEqual(len(convert_cram(data, selected_line=6)), 48)
        self.assertEqual(len(convert_cram(data, export_mode='all')), 7 * 48)

    def test_partial_last_row(self):
        data = bytes(4 * 32 + 6)
        info = inspect_cram(data)
        self.assertEqual(info['partial_colors'], 3)
        self.assertEqual(len(convert_cram(data, selected_line=4)), 9)

    def test_reject_odd_byte_file(self):
        with self.assertRaises(ValueError):
            inspect_cram(b'\x00\x01\x02')


if __name__ == '__main__':
    unittest.main()
