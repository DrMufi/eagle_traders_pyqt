import unittest
from product_management import ProductManagement  # But it's a widget, hard to test

# For math logic, create a separate function

def calculate_home_price(cost, packing, others, profit):
    return (cost + packing + others) + profit

def calculate_import_price(cost, carriage, profit):
    return cost + carriage + profit

class TestPricing(unittest.TestCase):
    def test_home_pricing(self):
        self.assertEqual(calculate_home_price(100, 10, 5, 20), 135)

    def test_import_pricing(self):
        self.assertEqual(calculate_import_price(100, 15, 20), 135)

if __name__ == '__main__':
    unittest.main()