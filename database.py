import random, mysql.connector as mc

def db_init():
    return mc.connect(
    host='shuttle.proxy.rlwy.net',
    port=22286,
    user='root',
    password='VXLTnudZeItLAsYwhJPROhRTmsZCSjCs',
    database='railway')


db = db_init()

cursor = db.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                    id  INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50) NOT NULL,
                    lrn_number VARCHAR(12) NOT NULL,
                    phone_number VARCHAR(12) NOT NULL,
                    email VARCHAR(55) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    grade_level VARCHAR(12) NOT NULL,
                    section VARCHAR(12) NOT NULL,
                    adviser_name VARCHAR(50) NOT NULL,
                    parent_phone_number VARCHAR(12) NOT NULL,
                    parent_facebook_link VARCHAR(155) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ); """)

# Add password column if it doesn't exist
try:
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password VARCHAR(255) NOT NULL DEFAULT ''")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS UNIQUE KEY unique_email (email)")
except Exception as e:
    print(f"Note: Some columns may already exist: {e}")




cursor.execute("""                
                CREATE TABLE IF NOT EXISTS books(
                    id  INT AUTO_INCREMENT PRIMARY KEY,
                    level INT(2),
                    strand VARCHAR(30),
                    title VARCHAR(55),
                    qtr VARCHAR(12),
                    description VARCHAR(50),
                    quantity INT(12),
                    publisher VARCHAR(24),
                    link VARCHAR(155),
                    bookType VARCHAR(20),
                    genre VARCHAR(30),
                    cover VARCHAR(255)
                );
                """)


cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin(
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL
                );
                """)

# Add missing columns to existing books table if they don't exist
try:
    cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS bookType VARCHAR(20)")
    cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS genre VARCHAR(30)")
    cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS cover VARCHAR(255)")
    
    # Check if quarter column exists and rename it to qtr
    cursor.execute("SHOW COLUMNS FROM books LIKE 'quarter'")
    if cursor.fetchone():
        print("Renaming 'quarter' column to 'qtr'...")
        cursor.execute("ALTER TABLE books CHANGE quarter qtr VARCHAR(12)")
        print("Column renamed successfully!")
    
except Exception as e:
    print(f"Note: Some columns may already exist: {e}")

cursor.close()
db.close()
