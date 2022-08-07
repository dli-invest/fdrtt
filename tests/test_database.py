# test cases for DB_MANAGER class in database.py using unittest
from random import random
import unittest
from database import DB_MANAGER

class DB_MANAGER_TESTS(unittest.TestCase):
    def setUp(self):
        self.db_manager = DB_MANAGER()

    def test_create_connection_pool(self):
        self.assertIsNotNone(self.db_manager.get_connection_pool())

    def test_create_tables(self):
        self.db_manager.create_tables("KWMqeJiIiMo")
        self.assertTrue(True)

    def test_clear_table(self):
        rand_num = random()
        test_name = "test_clear_table_" + str(rand_num)
        self.db_manager.create_tables(test_name)
        self.db_manager.clear_table(test_name)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
