from flask import Flask, request, jsonify, send_from_directory, session
from database import db_init
import os
from flask_cors import CORS
from datetime import datetime
import hashlib
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'fk9lratv113023'

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000", "http://127.0.0.1:5500", "http://127.0.0.1:5501", "http://localhost:5501"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'databasecontent', 'cover')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename to avoid conflicts"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}.{ext}"

# Existing routes...

@app.route('/api/books', methods=['GET'])
def api_books():
    db = db_init()
    cursor = db.cursor()
    cursor.execute("SHOW COLUMNS FROM books")
    cols = {row[0] for row in cursor.fetchall()}

    fields = [
        'id', 'level', 'strand', 'title',
        'quarter' if 'quarter' in cols else ('qtr' if 'qtr' in cols else None),
        'description', 'quantity', 'publisher',
        'cover' if 'cover' in cols else None,
        'link',
        'bookType' if 'bookType' in cols else None,
        'genre' if 'genre' in cols else None,
    ]
    select_fields = ", ".join([f for f in fields if f])
    cursor.execute(f"SELECT {select_fields} FROM books ORDER BY id DESC")
    rows = cursor.fetchall()
    desc = [d[0] for d in cursor.description]
    cursor.close()
    db.close()

    items = []
    for row in rows:
        rec = dict(zip(desc, row))
        rec['qtr'] = rec.get('quarter') if 'quarter' in rec else rec.get('qtr')
        if 'quarter' in rec:
            rec.pop('quarter', None)
        items.append({
            'id': rec.get('id'),
            'level': rec.get('level'),
            'strand': rec.get('strand'),
            'title': rec.get('title'),
            'qtr': rec.get('qtr'),
            'description': rec.get('description'),
            'quantity': rec.get('quantity'),
            'publisher': rec.get('publisher'),
            'cover': rec.get('cover'),
            'link': rec.get('link'),
            'bookType': rec.get('bookType'),
            'genre': rec.get('genre'),
        })
    return jsonify(items)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    db = db_init()
    cursor = db.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("SELECT id, email, first_name, last_name FROM users WHERE email=%s AND password=%s", (email, hashed_password))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not row:
        return jsonify({"error": "Invalid credentials"}), 401
    
    user_id, user_email, first_name, last_name = row
    
    session['user_id'] = user_id
    session['email'] = user_email
    session['first_name'] = first_name
    session['last_name'] = last_name
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user_id,
            "email": user_email,
            "first_name": first_name,
            "last_name": last_name
        }
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    
    required_fields = ['first_name', 'last_name', 'middle_name', 'email', 'password', 
                      'lrn_number', 'phone_number', 'adviser_name', 'grade_level', 
                      'section', 'parent_phone_number']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field.replace('_', ' ').title()} is required"}), 400
    
    db = db_init()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return jsonify({"error": "User with this email already exists"}), 409
    
    try:
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (first_name, last_name, middle_name, email, password, 
                             lrn_number, phone_number, adviser_name, grade_level, 
                             section, parent_phone_number, parent_facebook_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['first_name'], data['last_name'], data['middle_name'], data['email'],
            hashed_password, data['lrn_number'], data['phone_number'], data['adviser_name'],
            data['grade_level'], data['section'], data['parent_phone_number'],
            data.get('parent_facebook_link', '')
        ))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({
            "success": True,
            "message": "User registered successfully"
        }), 201
        
    except Exception as e:
        cursor.close()
        db.close()
        return jsonify({"error": "Registration failed. Please try again."}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({
        "success": True,
        "message": "Logout successful"
    })

@app.route('/api/databasecontent/cover/<filename>')
def serve_cover(filename):
    cover_dir = os.path.join(os.path.dirname(__file__), 'databasecontent', 'cover')
    return send_from_directory(cover_dir, filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/debug/admin-users', methods=['GET'])
def debug_admin_users():
    """Debug endpoint to check admin users in database"""
    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute("SELECT id, username FROM admin")
        admins = cursor.fetchall()
        
        admin_list = []
        for admin in admins:
            admin_list.append({
                "id": admin[0],
                "username": admin[1]
            })
        
        return jsonify({
            "admin_count": len(admin_list),
            "admins": admin_list
        })
    finally:
        cursor.close()
        db.close()

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    db = db_init()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.close()
        db.close()
        return jsonify({"error": "Book not found"}), 404
    
    cursor.execute("SHOW COLUMNS FROM books")
    cols = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    
    book_data = dict(zip(cols, row))
    return jsonify(book_data)

@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '')
    book_type = request.args.get('type', '')
    strand = request.args.get('strand', '')
    genre = request.args.get('genre', '')
    level = request.args.get('level', '')
    
    if not any([query, book_type, strand, genre, level]):
        return jsonify({"error": "At least one search parameter is required"}), 400
    
    db = db_init()
    cursor = db.cursor()
    
    sql = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (title LIKE %s OR description LIKE %s)"
        params.extend([f'%{query}%', f'%{query}%'])
    
    if book_type:
        sql += " AND bookType = %s"
        params.append(book_type)
    
    if strand:
        sql += " AND strand = %s"
        params.append(strand)
    
    if genre:
        sql += " AND genre = %s"
        params.append(genre)
    
    if level:
        sql += " AND level = %s"
        params.append(level)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    cursor.execute("SHOW COLUMNS FROM books")
    cols = [row[0] for row in cursor.fetchall()]
    cursor.close()
    db.close()
    
    books = []
    for row in rows:
        book_data = dict(zip(cols, row))
        books.append(book_data)
    
    return jsonify(books)

# Admin routes
@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.get_json() or {}
    username_data = data.get('username')
    password_data = data.get('password')
    
    print(f"DEBUG Login: Username={username_data}")
    
    if not username_data or not password_data:
        return jsonify({"error": "Username and password required"}), 400

    # Hash the password
    password_hash = hashlib.sha256(password_data.encode('utf-8')).hexdigest()

    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute(f"SELECT id, username, password FROM admin WHERE username='{username_data}' AND password='{password_hash}'")
        
        results = cursor.fetchall()
        print(f"DEBUG Login: Query results count: {len(results)}")
        
        if results:
            admin_id, username, password = results[0]
            session['admin_id'] = admin_id
            session['username'] = username
            print(f"DEBUG Login: Session set - admin_id={admin_id}, username={username}")
            print(f"DEBUG Login: Full session: {dict(session)}")
            return jsonify({
                "success": True, 
                "message": "Login successful",
                "admin_id": admin_id,
                "username": username
            })
        
        print("DEBUG Login: No matching user found")
        return jsonify({"error": "Invalid credentials"}), 401
        
    finally:
        cursor.close()
        db.close()

@app.route('/api/admin/profile', methods=['GET'])
def api_admin_profile():
    if not session.get('admin_id'):
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({
        "admin_id": session['admin_id'],
        "username": session.get('username')
    })

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    print(f"DEBUG Logout: Session before clear: {dict(session)}")
    session.clear()
    print(f"DEBUG Logout: Session after clear: {dict(session)}")
    return jsonify({"success": True, "message": "Logged out successfully"})

# Admin book management endpoints
@app.route('/api/admin/books', methods=['GET'])
def api_admin_get_books():

    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, bookType, level, strand, qtr, genre, 
                   description, quantity, publisher, cover
            FROM books 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        
        books = []
        for row in rows:
            books.append({
                'id': row[0],
                'title': row[1],
                'bookType': row[2],
                'level': row[3],
                'strand': row[4],
                'qtr': row[5],
                'genre': row[6],
                'description': row[7],
                'quantity': row[8],
                'publisher': row[9],
                'cover': row[10]
            })
        
        return jsonify(books)
    finally:
        cursor.close()
        db.close()

@app.route('/api/admin/books', methods=['POST'])
def api_admin_add_book():

    try:
        # Get form data
        title = request.form.get('title')
        book_type = request.form.get('bookType')
        description = request.form.get('description')
        quantity = request.form.get('quantity')
        publisher = request.form.get('publisher')
        
        # Validate required fields
        if not all([title, book_type, quantity, publisher]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Handle book type specific fields
        level = None
        strand = None
        qtr = None
        genre = None
        
        if book_type == 'Module':
            level = request.form.get('level')
            strand = request.form.get('strand')
            qtr = request.form.get('qtr')
            if not all([level, strand, qtr]):
                return jsonify({"error": "Module requires level, strand, and quarter"}), 400
        elif book_type == 'Novel':
            genre = request.form.get('genre')
            if not genre:
                return jsonify({"error": "Novel requires genre"}), 400
        
        # Handle cover upload
        cover_filename = None
        if 'cover' in request.files:
            cover_file = request.files['cover']
            if cover_file and cover_file.filename and allowed_file(cover_file.filename):
                cover_filename = generate_unique_filename(cover_file.filename)
                cover_file.save(os.path.join(UPLOAD_FOLDER, cover_filename))
        
        # Insert into database
        db = db_init()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO books (title, bookType, level, strand, qtr, genre, 
                              description, quantity, publisher, cover)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, book_type, level, strand, qtr, genre, 
              description, quantity, publisher, cover_filename))
        
        db.commit()
        book_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            "success": True,
            "message": "Book added successfully",
            "book_id": book_id
        }), 201
        
    except Exception as e:
        print(f"Error adding book: {e}")
        return jsonify({"error": "Failed to add book"}), 500

@app.route('/api/admin/books/<int:book_id>', methods=['GET'])
def api_admin_get_book(book_id):

    db = db_init()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, bookType, level, strand, qtr, genre, 
                   description, quantity, publisher, cover
            FROM books WHERE id = %s
        """, (book_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Book not found"}), 404
        
        book = {
            'id': row[0],
            'title': row[1],
            'bookType': row[2],
            'level': row[3],
            'strand': row[4],
            'qtr': row[5],
            'genre': row[6],
            'description': row[7],
            'quantity': row[8],
            'publisher': row[9],
            'cover': row[10]
        }
        
        return jsonify(book)
    finally:
        cursor.close()
        db.close()

@app.route('/api/admin/books/<int:book_id>', methods=['PUT'])
def api_admin_update_book(book_id):

    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'bookType', 'quantity', 'publisher']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Handle book type specific validation
        if data['bookType'] == 'Module':
            if not all([data.get('level'), data.get('strand'), data.get('qtr')]):
                return jsonify({"error": "Module requires level, strand, and quarter"}), 400
        elif data['bookType'] == 'Novel':
            if not data.get('genre'):
                return jsonify({"error": "Novel requires genre"}), 400
        
        # Update database
        db = db_init()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE books 
            SET title = %s, bookType = %s, level = %s, strand = %s, qtr = %s, 
                genre = %s, description = %s, quantity = %s, publisher = %s
            WHERE id = %s
        """, (
            data['title'], data['bookType'], data.get('level'), data.get('strand'),
            data.get('qtr'), data.get('genre'), data.get('description', ''),
            data['quantity'], data['publisher'], book_id
        ))
        
        # Handle cover update if provided
        if data.get('cover'):
            cursor.execute("UPDATE books SET cover = %s WHERE id = %s", 
                          (data['cover'], book_id))
        
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({
            "success": True,
            "message": "Book updated successfully"
        })
        
    except Exception as e:
        print(f"Error updating book: {e}")
        return jsonify({"error": "Failed to update book"}), 500

@app.route('/api/admin/books/<int:book_id>', methods=['DELETE'])
def api_admin_delete_book(book_id):

    db = db_init()
    cursor = db.cursor()
    
    try:
        # Get cover filename before deletion
        cursor.execute("SELECT cover FROM books WHERE id = %s", (book_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Book not found"}), 404
        
        # Delete cover file if it exists
        cover_filename = row[0]
        if cover_filename:
            cover_path = os.path.join(UPLOAD_FOLDER, cover_filename)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        # Delete from database
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Book deleted successfully"
        })
        
    except Exception as e:
        print(f"Error deleting book: {e}")
        return jsonify({"error": "Failed to delete book"}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/api/admin/books/upload-cover', methods=['POST'])
def api_admin_upload_cover():

    if 'cover' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    cover_file = request.files['cover']
    if cover_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(cover_file.filename):
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400
    
    try:
        filename = generate_unique_filename(cover_file.filename)
        cover_file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        return jsonify({
            "success": True,
            "filename": filename,
            "message": "Cover uploaded successfully"
        })
        
    except Exception as e:
        print(f"Error uploading cover: {e}")
        return jsonify({"error": "Failed to upload cover"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)