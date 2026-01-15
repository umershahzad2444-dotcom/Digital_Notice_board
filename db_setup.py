import pyodbc
from database import get_db_connection

SERVER_NAME = 'MALIKZADA\\AMINASHAHZAD'

def create_database_if_not_exists():
    # Silent check unless error or creation
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
        conn.close()
    except Exception as e:
        print(f"[FAIL] Failed to create database: {e}")
        return False
    return True

def init_tables():
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[FAIL] Connection FAILED: {e}")
        return

    cursor = conn.cursor()
    
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
    except Exception as e:
        print(f"[FAIL] User Table Error: {e}")

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
            ExpiryDate DATETIME NULL,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
        ELSE
        BEGIN
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Notifications') AND name = 'ExpiryDate')
            ALTER TABLE Notifications ADD ExpiryDate DATETIME NULL
        END
        """)
    except Exception as e:
        print(f"[FAIL] Notifications Table Error: {e}")

    # Create Default Admin
    try:
        cursor.execute("SELECT * FROM Users WHERE Email = 'admin@gmail.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Users (FullName, Email, Password, Role, IsApproved) VALUES ('Admin', 'admin@gmail.com', 'admin123', 'Admin', 1)")
            print("[INFO] Default Admin account created.")
    except Exception as e:
         print(f"[FAIL] Admin Creation Error: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    if create_database_if_not_exists():
        init_tables()
