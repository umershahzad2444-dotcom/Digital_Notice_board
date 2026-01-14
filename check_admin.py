from database import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE Email = 'admin@gmail.com'")
    user = cursor.fetchone()
    if user:
        print("[OK] Admin Found: " + str(user))
    else:
        print("[FAIL] Admin NOT Found!")
    conn.close()
except Exception as e:
    print(f"[FAIL] DB Error: {e}")
