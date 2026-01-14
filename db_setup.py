import pyodbc
from database import get_db_connection

SERVER_NAME = 'MALIKZADA\\AMINASHAHZAD'

def create_database_if_not_exists():
    print("--- 0. Checking Database Existence ---")
    # Connect to 'master' to create the DB
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={SERVER_NAME};'
        'DATABASE=master;'
        'Trusted_Connection=yes;'
        'AutoCommit=True;'
    )
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        cursor.execute("IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'NoticeBoardDB') CREATE DATABASE NoticeBoardDB")
        print("[OK] Database 'NoticeBoardDB' checked/created.")
        conn.close()
    except Exception as e:
        print(f"[FAIL] Failed to create database: {e}")
        return False
    return True

def init_tables():
    print("\n--- 1. Testing Connection to NoticeBoardDB ---")
    try:
        # Now connect effectively using the function in database.py 
        # (Assuming it points to NoticeBoardDB, which we just ensured exists)
        conn = get_db_connection()
        print("[OK] Connection Successful!")
    except Exception as e:
        print(f"[FAIL] Connection FAILED: {e}")
        return

    cursor = conn.cursor()

    print("\n--- 2. Checking/Creating Tables ---")
    
    # Table: Users
    try:
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
        CREATE TABLE Users (
            UserID INT IDENTITY(1,1) PRIMARY KEY,
            FullName NVARCHAR(100),
            Email NVARCHAR(100) UNIQUE,
            Password NVARCHAR(100),
            Role NVARCHAR(50), -- 'Admin' or 'Student'
            IsApproved BIT DEFAULT 0
        )
        """)
        print("[OK] Table 'Users' checked/created.")
    except Exception as e:
        print(f"[FAIL] Failed to check/create 'Users' table: {e}")

    # Table: Notifications
    try:
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Notifications' AND xtype='U')
        CREATE TABLE Notifications (
            id INT IDENTITY(1,1) PRIMARY KEY,
            Title NVARCHAR(200),
            Content NVARCHAR(MAX),
            Category NVARCHAR(50),
            Attachment NVARCHAR(200),
            CreatedAt DATETIME DEFAULT GETDATE()
        )
        """)
        print("[OK] Table 'Notifications' checked/created.")
    except Exception as e:
        print(f"[FAIL] Failed to check/create 'Notifications' table: {e}")

    # Create Default Admin
    try:
         # Check if admin exists
        cursor.execute("SELECT * FROM Users WHERE Email = 'admin@gmail.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Users (FullName, Email, Password, Role, IsApproved) VALUES ('Admin', 'admin@gmail.com', 'admin123', 'Admin', 1)")
            print("[OK] Default Admin account created (admin@gmail.com / admin123).")
        else:
            print("[INFO] Admin account already exists.")
    except Exception as e:
         print(f"[FAIL] Failed to create admin: {e}")

    conn.commit()
    conn.close()
    print("\n--- Database Setup Complete ---")

if __name__ == "__main__":
    if create_database_if_not_exists():
        init_tables()
