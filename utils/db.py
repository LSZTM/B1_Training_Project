import pyodbc
import streamlit as st
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Constants ─────────────────────────────────────────────────────────────────
LEGACY_CONNECTION_STRINGS = [
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
]
SESSION_CONN_STR_KEY = "db_connection_string"
SESSION_DB_NAME_KEY = "db_selected_database"
SESSION_SERVER_KEY = "db_selected_server"


def requires_sql_auth(server):
    """Ngrok TCP endpoints cannot use local Windows/SSPI credentials."""
    return "ngrok" in str(server or "").lower()

# ── Available ODBC drivers ────────────────────────────────────────────────────
def get_available_drivers():
    """Return a list of installed SQL Server ODBC drivers."""
    try:
        all_drivers = pyodbc.drivers()
        return [d for d in all_drivers if "sql" in d.lower()]
    except Exception:
        return ["{ODBC Driver 17 for SQL Server}", "{SQL Server}"]

# ── Connection string builder ─────────────────────────────────────────────────
def build_connection_string(server, database, driver=None, username=None, password=None):
    """Build a pyodbc connection string from components."""
    if not driver:
        drivers = get_available_drivers()
        driver = drivers[0] if drivers else "{ODBC Driver 17 for SQL Server}"
    # Ensure driver is wrapped in braces
    if not driver.startswith("{"):
        driver = "{" + driver + "}"
    if username or password:
        if not username or not password:
            raise ValueError("SQL Server Authentication requires both username and password.")
        return f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
    if requires_sql_auth(server):
        raise ValueError("Ngrok SQL Server connections require SQL Server Authentication. Windows Authentication cannot cross the ngrok TCP tunnel.")
    return f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;"

# ── Cache helpers ─────────────────────────────────────────────────────────────
def _get_cached_connection_string():
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if not get_script_run_ctx():
        return None
        
    try:
        return st.session_state.get(SESSION_CONN_STR_KEY, None)
    except Exception:
        return None

def _set_cached_connection_string(conn_str):
    try:
        st.session_state[SESSION_CONN_STR_KEY] = conn_str
    except Exception:
        pass

# ── Discover a working server connection ──────────────────────────────────────
def discover_server_connection(server=None, driver=None, username=None, password=None):
    """
    Try to connect to a SQL Server instance using `master` database.
    Returns the working connection string on success, or raises ConnectionError.
    """
    target_server = server or os.environ.get("DB_SERVER")
    target_driver = driver or os.environ.get("DB_DRIVER")
    target_user = username or os.environ.get("DB_USERNAME")
    target_pass = password or os.environ.get("DB_PASSWORD")

    if target_server:
        try:
            conn_str = build_connection_string(target_server, "master", target_driver, target_user, target_pass)
        except ValueError as e:
            raise ConnectionError(str(e))
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            conn.close()
            return conn_str
        except pyodbc.Error as e:
            raise ConnectionError(f"Cannot reach server '{target_server}': {e}")

    # Fallback: try legacy local strings with master
    for driver_opt in get_available_drivers():
        for srv in ["localhost\\SQLEXPRESS", "localhost", "."]:
            conn_str = build_connection_string(srv, "master", driver_opt)
            try:
                conn = pyodbc.connect(conn_str, timeout=5)
                conn.close()
                return conn_str
            except pyodbc.Error:
                continue

    raise ConnectionError("No reachable SQL Server instance found.")

# ── List databases on a server ────────────────────────────────────────────────
def list_databases(server_conn_str=None, server=None, driver=None, username=None, password=None):
    """
    Return a list of user database names from the connected SQL Server instance.
    Connects to `master` to enumerate databases.
    """
    if not server_conn_str:
        server_conn_str = discover_server_connection(server, driver, username, password)
    try:
        conn = pyodbc.connect(server_conn_str, timeout=10)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name"
        )
        databases = [row[0] for row in cursor.fetchall()]
        conn.close()
        return databases
    except pyodbc.Error as e:
        raise ConnectionError(f"Failed to list databases: {e}")

# ── Switch to a specific database ─────────────────────────────────────────────
def switch_database(database, server=None, driver=None, username=None, password=None):
    """
    Build and cache a connection string targeting a specific database.
    Returns True on success.
    """
    global MODULE_CONN_STR_CACHE

    target_server = server or st.session_state.get(SESSION_SERVER_KEY) or os.environ.get("DB_SERVER")
    target_driver = driver or os.environ.get("DB_DRIVER")
    target_user = username or os.environ.get("DB_USERNAME")
    target_pass = password or os.environ.get("DB_PASSWORD")

    if not target_server:
        # Attempt to detect from legacy fallback
        try:
            master_str = discover_server_connection()
            # Extract server from the discovered string
            for part in master_str.split(";"):
                if part.upper().startswith("SERVER="):
                    target_server = part.split("=", 1)[1]
                    break
        except ConnectionError:
            raise ConnectionError("No server configured and local discovery failed.")

    try:
        conn_str = build_connection_string(target_server, database, target_driver, target_user, target_pass)
    except ValueError as e:
        raise ConnectionError(str(e))
    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        conn.close()
        _set_cached_connection_string(conn_str)
        try:
            st.session_state[SESSION_DB_NAME_KEY] = database
            st.session_state[SESSION_SERVER_KEY] = target_server
        except Exception:
            pass
        return True
    except pyodbc.Error as e:
        raise ConnectionError(f"Cannot connect to database '{database}': {e}")

# ── Primary connection discovery (backwards compatible) ───────────────────────
def discover_working_connection_string():
    cached = _get_cached_connection_string()
    if cached:
        return cached

    # 1. Try Environment Variables
    env_server = os.environ.get("DB_SERVER")
    env_database = os.environ.get("DB_DATABASE", "QUERY_PRACTICE")
    env_driver = os.environ.get("DB_DRIVER")
    env_username = os.environ.get("DB_USERNAME")
    env_password = os.environ.get("DB_PASSWORD")

    if env_server:
        try:
            conn_str = build_connection_string(env_server, env_database, env_driver, env_username, env_password)
        except ValueError as e:
            raise ConnectionError(str(e))
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            conn.close()
            _set_cached_connection_string(conn_str)
            try:
                st.session_state[SESSION_DB_NAME_KEY] = env_database
                st.session_state[SESSION_SERVER_KEY] = env_server
            except Exception:
                pass
            return conn_str
        except pyodbc.Error as e:
            raise ConnectionError(f"Failed to connect using environment variables: {e}")

    # 2. Local Fallback Strings
    for conn_str in LEGACY_CONNECTION_STRINGS:
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            conn.close()
            _set_cached_connection_string(conn_str)
            try:
                st.session_state[SESSION_DB_NAME_KEY] = "QUERY_PRACTICE"
            except Exception:
                pass
            return conn_str
        except pyodbc.Error:
            continue

    raise ConnectionError("All SQL Server connection strings failed. Check your local SQL server or .env configuration.")


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
        try:
            st.session_state[SESSION_DB_NAME_KEY] = database
        except Exception:
            pass
        return {"success": True, "database": database, "connection_string": _get_cached_connection_string()}
    except Exception as err:
        return {"success": False, "error": str(err)}
    finally:
        close_connection(conn)

def get_current_database_name():
    """Get the currently selected database name for display."""
    try:
        return st.session_state.get(SESSION_DB_NAME_KEY, "Not selected")
    except Exception:
        return "Not selected"
