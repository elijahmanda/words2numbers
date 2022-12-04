from unittest import TestCase

from words2numbers import words2numbers as w2n
from words2numbers.utils import align_results, tuple_map

NUM_INTEGER = ("number", "integer")
NUM_FLOAT = ("number", "float")


class TestBase(TestCase):
    
    def test_ones_string(self):
        query = "one two three neg four five six seven eight nine zero"
        res = tuple_map(align_results,w2n(query))
        self.assertTupleEqual(res,
            (("one", 1, *NUM_INTEGER),
            ("two", 2, *NUM_INTEGER),
            ("three", 3, *NUM_INTEGER),
            ("four", 4, *NUM_INTEGER),
            ("five", 5, *NUM_INTEGER),
            ("six", 6, *NUM_INTEGER),
            ("seven", 7, *NUM_INTEGER),
            ("eight", 8, *NUM_INTEGER),
            ("nine", 9, *NUM_INTEGER),
            ("zero", 0, *NUM_INTEGER))
        )
    
    def test_ones_number(self):
        query = "1 2 3 4 5 6 7 8 9 0"
        res = tuple_map(align_results,w2n(query))
        self.assertTupleEqual(res,
            (("1", 1, *NUM_INTEGER),
            ("2", 2, *NUM_INTEGER),
            ("3", 3, *NUM_INTEGER),
            ("4", 4, *NUM_INTEGER),
            ("5", 5, *NUM_INTEGER),
            ("6", 6, *NUM_INTEGER),
            ("7", 7, *NUM_INTEGER),
            ("8", 8, *NUM_INTEGER),
            ("9", 9, *NUM_INTEGER),
            ("0", 0, *NUM_INTEGER))
        )
        
    def test_ones_string_negative(self):
        query = "negative one neg two minus three neg four minus five negative six neg seven minus eight minus nine"
        res = tuple_map(align_results,w2n(query))
        self.assertTupleEqual(res,
            (("negative one", -1, *NUM_INTEGER),
            ("neg two", -2, *NUM_INTEGER),
            ("minus three", -3, *NUM_INTEGER),
            ("neg four", -4, *NUM_INTEGER),
            ("minus five", -5, *NUM_INTEGER),
            ("negative six", -6, *NUM_INTEGER),
            ("neg seven", -7, *NUM_INTEGER),
            ("minus eight", -8, *NUM_INTEGER),
            ("minus nine", -9, *NUM_INTEGER))
        )
        
    def test_ten_and_teens_string(self):
        query = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
        res = tuple_map(align_results,w2n(query))
        self.assertTupleEqual(res,
            (("ten", 10, *NUM_INTEGER),
            ("eleven", 11, *NUM_INTEGER),
            ("twelve", 12, *NUM_INTEGER),
            ("thirteen", 13, *NUM_INTEGER),
            ("fourteen", 14, *NUM_INTEGER),
            ("fifteen", 15, *NUM_INTEGER),
            ("sixteen", 16, *NUM_INTEGER),
            ("seventeen", 17, *NUM_INTEGER),
            ("eighteen", 18, *NUM_INTEGER),
            ("nineteen", 19, *NUM_INTEGER))
        )
        

if __name__=="__main__":
    import unittest
    unittest.main()