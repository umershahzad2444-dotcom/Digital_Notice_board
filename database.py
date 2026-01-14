import pyodbc

def get_db_connection():
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=MALIKZADA\\AMINASHAHZAD;'
        'DATABASE=NoticeBoardDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)