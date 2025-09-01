#!/usr/bin/env python3
"""
Admin Registration Script
This script allows you to register new admin users or update existing admin passwords.
"""

from database import db_init
import hashlib
import getpass
import sys

def hash_password(password, algorithm='sha256'):
    """Hash password using specified algorithm"""
    if algorithm == 'md5':
        return hashlib.md5(password.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(password.encode()).hexdigest()
    else:
        raise ValueError("Unsupported algorithm. Use 'md5' or 'sha256'")

def check_admin_exists(username):
    """Check if admin username already exists"""
    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT id, username FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        return admin is not None
    finally:
        cursor.close()
        db.close()

def register_admin(username, password, algorithm='sha256'):
    """Register a new admin user"""
    db = db_init()
    cursor = db.cursor()
    
    try:
        # Hash the password
        hashed_password = hash_password(password, algorithm)
        
        # Insert new admin
        cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", 
                      (username, hashed_password))
        db.commit()
        
        print(f" Admin '{username}' registered successfully!")
        print(f"   Password hashed using: {algorithm.upper()}")
        print(f"   Hash: {hashed_password}")
        return True
        
    except Exception as e:
        print(f" Error registering admin: {str(e)}")
        db.rollback()
        return False
    finally:
        cursor.close()
        db.close()

def update_admin_password(username, new_password, algorithm='sha256'):
    """Update existing admin password"""
    db = db_init()
    cursor = db.cursor()
    
    try:
        # Hash the new password
        hashed_password = hash_password(new_password, algorithm)
        
        # Update admin password
        cursor.execute("UPDATE admin SET password=%s WHERE username=%s", 
                      (hashed_password, username))
        
        if cursor.rowcount > 0:
            db.commit()
            print(f" Password updated for admin '{username}'!")
            print(f"   New password hashed using: {algorithm.upper()}")
            print(f"   New hash: {hashed_password}")
            return True
        else:
            print(f" Admin '{username}' not found")
            return False
            
    except Exception as e:
        print(f" Error updating password: {str(e)}")
        db.rollback()
        return False
    finally:
        cursor.close()
        db.close()

def list_admins():
    """List all existing admin users"""
    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT id, username, password FROM admin ORDER BY id")
        admins = cursor.fetchall()
        
        if not admins:
            print(" No admin users found")
            return
        
        print(f" Found {len(admins)} admin user(s):")
        print("-" * 60)
        print(f"{'ID':<5} {'Username':<20} {'Password Hash':<40} {'Algorithm'}")
        print("-" * 60)
        
        for admin in admins:
            admin_id, username, password_hash = admin
            hash_length = len(password_hash) if password_hash else 0
            
            # Determine algorithm based on hash length
            if hash_length == 32:
                algorithm = "MD5"
            elif hash_length == 64:
                algorithm = "SHA-256"
            elif hash_length == 30:
                algorithm = "MD5 (30)"
            else:
                algorithm = "Unknown"
            
            print(f"{admin_id:<5} {username:<20} {password_hash:<40} {algorithm}")
        
    except Exception as e:
        print(f" Error listing admins: {str(e)}")
    finally:
        cursor.close()
        db.close()

def main():
    """Main function"""
    print(" Admin Registration Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Register new admin")
        print("2. Update admin password")
        print("3. List all admins")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            # Register new admin
            print("\n Register New Admin")
            print("-" * 30)
            
            username = input("Enter username: ").strip()
            if not username:
                print(" Username cannot be empty")
                continue
            
            if check_admin_exists(username):
                print(f" Admin '{username}' already exists")
                continue
            
            password = getpass.getpass("Enter password: ").strip()
            if not password:
                print(" Password cannot be empty")
                continue
            
            confirm_password = getpass.getpass("Confirm password: ").strip()
            if password != confirm_password:
                print(" Passwords do not match")
                continue
            
            print("\nHash algorithm options:")
            print("1. SHA-256 (recommended, 64 characters)")
            print("2. MD5 (32 characters)")
            print("3. MD5 truncated to 30 characters")
            
            algo_choice = input("Choose algorithm (1-3, default 1): ").strip()
            
            if algo_choice == '2':
                algorithm = 'md5'
            elif algo_choice == '3':
                algorithm = 'md5_truncated'
            else:
                algorithm = 'sha256'
            
            if algorithm == 'md5_truncated':
                # Special case for truncated MD5
                hashed_password = hashlib.md5(password.encode()).hexdigest()[:30]
                db = db_init()
                cursor = db.cursor()
                
                try:
                    cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", 
                                  (username, hashed_password))
                    db.commit()
                    print(f"   Admin '{username}' registered successfully!")
                    print(f"   Password hashed using: MD5 (truncated to 30 chars)")
                    print(f"   Hash: {hashed_password}")
                except Exception as e:
                    print(f" Error registering admin: {str(e)}")
                    db.rollback()
                finally:
                    cursor.close()
                    db.close()
            else:
                register_admin(username, password, algorithm)
        
        elif choice == '2':
            # Update admin password
            print("\n Update Admin Password")
            print("-" * 30)
            
            username = input("Enter username: ").strip()
            if not username:
                print(" Username cannot be empty")
                continue
            
            if not check_admin_exists(username):
                print(f" Admin '{username}' not found")
                continue
            
            new_password = getpass.getpass("Enter new password: ").strip()
            if not new_password:
                print(" Password cannot be empty")
                continue
            
            confirm_password = getpass.getpass("Confirm new password: ").strip()
            if new_password != confirm_password:
                print(" Passwords do not match")
                continue
            
            print("\nHash algorithm options:")
            print("1. SHA-256 (recommended, 64 characters)")
            print("2. MD5 (32 characters)")
            print("3. MD5 truncated to 30 characters")
            
            algo_choice = input("Choose algorithm (1-3, default 1): ").strip()
            
            if algo_choice == '2':
                algorithm = 'md5'
            elif algo_choice == '3':
                algorithm = 'md5_truncated'
            else:
                algorithm = 'sha256'
            
            if algorithm == 'md5_truncated':
                # Special case for truncated MD5
                hashed_password = hashlib.md5(new_password.encode()).hexdigest()[:30]
                update_admin_password(username, hashed_password, 'plain')
            else:
                update_admin_password(username, new_password, algorithm)
        
        elif choice == '3':
            # List all admins
            print("\n Listing All Admins")
            print("-" * 30)
            list_admins()
        
        elif choice == '4':
            print("\n Lami xox <3 by aczon <3 bisayang binalibag")
            break
        
        else:
            print(" Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n Unexpected error: {str(e)}")
        sys.exit(1)
