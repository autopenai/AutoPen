#!/usr/bin/env python3
"""
Simple test server with a vulnerable login page for testing the SQL injection agent.

Prerequisites:
    pip install flask

Usage:
    python test_server.py
    
Then run the agent with:
    python agent_with_playwright.py http://localhost:8080/login
"""

from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Create a simple in-memory database for testing
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'secret123')")
    cursor.execute("INSERT INTO users (username, password) VALUES ('user', 'password')")
    conn.commit()
    return conn

# Global database connection for this demo
db_conn = init_db()

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Login Page</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
        .form-group { margin: 15px 0; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; margin: 5px 0; }
        input[type="submit"] { background: #007cba; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
    </style>
</head>
<body>
    <h2>Login Page</h2>
    <form method="POST" action="/login">
        <div class="form-group">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
        </div>
        <div class="form-group">
            <input type="submit" value="Login">
        </div>
    </form>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <p><small>Valid credentials: admin/secret123 or user/password</small></p>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .success { color: green; font-size: 18px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Welcome to the Dashboard!</h1>
    <div class="success">✅ Login successful! You are now authenticated.</div>
    <p>Username: {{ username }}</p>
    <p>This page confirms that authentication was bypassed.</p>
    <a href="/logout">Logout</a>
</body>
</html>
'''

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template_string(LOGIN_TEMPLATE)
    
    username = request.form['username']
    password = request.form['password']
    
    # VULNERABLE SQL QUERY - DO NOT USE IN PRODUCTION!
    # This is intentionally vulnerable for testing purposes
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    
    print(f"Executing query: {query}")  # Debug output
    
    try:
        cursor = db_conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            # Login successful - redirect to dashboard
            return render_template_string(DASHBOARD_TEMPLATE, username=username)
        else:
            # Login failed
            return render_template_string(LOGIN_TEMPLATE, error="Invalid username or password")
    
    except Exception as e:
        print(f"SQL Error: {e}")
        return render_template_string(LOGIN_TEMPLATE, error="Database error occurred")

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("🚀 Starting vulnerable test server on http://localhost:8080")
    print("📝 Valid credentials: admin/secret123 or user/password")
    print("⚠️  This server is intentionally vulnerable for testing purposes!")
    print("🔍 Try the SQL injection: username='admin', password=' OR 1=1--")
    app.run(host='0.0.0.0', port=8080, debug=True) 