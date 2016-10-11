#!/usr/bin/env python3
# coding: utf-8

"""
Convenient database wrapper.
"""

import sqlite3


class Database:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def quick_check(self):
        """
        https://www.sqlite.org/pragma.html#pragma_quick_check
        """
        self.connection.execute("PRAGMA quick_check")

    def close(self):
        self.connection.close()
