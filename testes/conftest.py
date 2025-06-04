import unittest
from database.db_handler import initialize_database

def setUpModule():
    initialize_database()
