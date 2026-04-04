"""Backward-compatible DB test helpers.

Prefer importing from utils.db directly.
"""

import pyodbc

from utils.db import close_connection, discover_working_connection_string, get_connection, test_connection


def get_available_drivers():
    """List SQL Server drivers."""
    drivers = pyodbc.drivers()
    return [d for d in drivers if "SQL Server" in d or "ODBC Driver" in d]
