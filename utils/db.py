import pyodbc
import streamlit as st

def get_connection():
    """Get database connection with proper error handling"""
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=QUERY_PRACTICE;"
            "Trusted_Connection=yes;"
            "Connection Timeout=30;"
        )
        conn = pyodbc.connect(conn_str, timeout=30)
        st.session_state.connection_status = True
        return conn
    except pyodbc.Error as e:
        st.session_state.connection_status = False
        st.error(f"❌ Database connection failed: {str(e)}")
        st.info("🔧 Check: SQL Server running, ODBC Driver 17 installed, QUERY_PRACTICE database exists")
        return None
    except Exception as e:
        st.session_state.connection_status = False
        st.error(f"❌ Connection error: {str(e)}")
        return None

def close_connection(conn):
    """Close database connection safely"""
    if conn:
        try:
            conn.close()
        except:
            pass

def test_connection():
    """Test connection and update session state"""
    conn = get_connection()
    if conn:
        close_connection(conn)
        return True
    return False
