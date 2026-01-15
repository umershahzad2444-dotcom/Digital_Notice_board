import pyodbc
import sys
import time

def test_connection():
    server = 'MALIKZADA\\AMINASHAHZAD'
    print(f"Testing connection to server: {server}...")
    
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={server};'
        'DATABASE=master;'
        'Trusted_Connection=yes;'
    )
    
    start = time.time()
    try:
        print("Attempting to connect (timeout defaults to driver setting)...")
        # specific timeout to fail fast if possible, though ODBC driver handles it
        conn = pyodbc.connect(conn_str, timeout=10) 
        print(f"SUCCESS: Connected to SQL Server in {time.time() - start:.2f} seconds.")
        conn.close()
    except Exception as e:
        print(f"FAILURE: Could not connect. Error: {e}")
        print(f"Time taken: {time.time() - start:.2f} seconds.")

if __name__ == "__main__":
    test_connection()
