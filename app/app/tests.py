"""
Sample Test
"""

from django.test import SimpleTestCase
from . import calc


class CalcTests(SimpleTestCase):
    def test_add_two_numbers(self):
        res = calc.add(5,6)
        self.assertEqual(res,11)
    
    def test_sub_two_numbers(self):
        res = calc.subtract(7,5)
        self.assertEqual(res,2)