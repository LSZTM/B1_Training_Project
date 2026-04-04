import pyodbc
import streamlit as st

WORKING_CONNECTION_STRINGS = [
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
]
SESSION_CONN_STR_KEY = "db_connection_string"
MODULE_CONN_STR_CACHE = None


def _get_cached_connection_string():
    global MODULE_CONN_STR_CACHE
    try:
        if SESSION_CONN_STR_KEY in st.session_state:
            MODULE_CONN_STR_CACHE = st.session_state[SESSION_CONN_STR_KEY]
            return MODULE_CONN_STR_CACHE
    except Exception:
        pass
    return MODULE_CONN_STR_CACHE


def _set_cached_connection_string(conn_str):
    global MODULE_CONN_STR_CACHE
    MODULE_CONN_STR_CACHE = conn_str
    try:
        st.session_state[SESSION_CONN_STR_KEY] = conn_str
    except Exception:
        pass


def discover_working_connection_string():
    cached = _get_cached_connection_string()
    if cached:
        return cached

    for conn_str in WORKING_CONNECTION_STRINGS:
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            conn.close()
            _set_cached_connection_string(conn_str)
            return conn_str
        except pyodbc.Error:
            continue

    raise ConnectionError("All SQL Server connection strings failed.")


def get_connection():
    """Get database connection using discovered and cached connection string."""
    conn_str = discover_working_connection_string()
    try:
        return pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as err:
        if _get_cached_connection_string() == conn_str:
            try:
                st.session_state.pop(SESSION_CONN_STR_KEY, None)
            except Exception:
                pass
        raise ConnectionError(f"Database connection failed using cached string: {err}") from err

def close_connection(conn):
    """Close database connection safely"""
    if conn:
        try:
            conn.close()
        except:
            pass

def test_connection():
    """Test if a database connection is available."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT DB_NAME()")
            database = cursor.fetchone()[0]
        return {"success": True, "database": database, "connection_string": _get_cached_connection_string()}
    except Exception as err:
        return {"success": False, "error": str(err)}
    finally:
        close_connection(conn)
