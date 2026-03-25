# test_connection.py - Pure functions (no Streamlit)
import pyodbc

# Working connection strings (from your test)
WORKING_CONNECTION_STRINGS = [
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
    "DRIVER={SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=QUERY_PRACTICE;Trusted_Connection=yes;",
]

def get_connection():
    """Try all connection strings, return first working one"""
    for conn_str in WORKING_CONNECTION_STRINGS:
        try:
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT DB_NAME() as database_name")
            db_name = cursor.fetchone()[0]
            print(f"✅ Connected to: {db_name} using: {conn_str}")
            return conn  # Return OPEN connection
        except Exception as e:
            print(f"❌ Failed: {conn_str} - {str(e)}")
            continue
    return None

def close_connection(conn):
    """Safely close connection"""
    if conn:
        try:
            conn.close()
        except:
            pass

def test_connection():
    """Test if any connection works - returns dict for service layer"""
    conn = get_connection()
    if conn:
        close_connection(conn)
        return {"success": True, "database": "QUERY_PRACTICE"}
    return {"success": False, "error": "All connection strings failed"}

def get_available_drivers():
    """List SQL Server drivers"""
    try:
        drivers = pyodbc.drivers()
        sql_drivers = [d for d in drivers if "SQL Server" in d or "ODBC Driver" in d]
        return sql_drivers
    except:
        return []
