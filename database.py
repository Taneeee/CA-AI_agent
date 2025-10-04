# database.py
import sqlite3
import os

def init_db():
    """Initialize the database with the user_profiles table"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            monthly_income REAL,
            monthly_expenses REAL,
            current_savings REAL,
            risk_profile TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_user(name, income, expenses, savings, risk_profile):
    """Insert a new user profile into the database"""
    if not os.path.exists('users.db'):
        init_db()
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_profiles (name, monthly_income, monthly_expenses, current_savings, risk_profile)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, income, expenses, savings, risk_profile))
    conn.commit()
    conn.close()

def get_all_users():
    """Retrieve all user profiles from database"""
    if not os.path.exists('users.db'):
        init_db()
        return []
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user_profiles ORDER BY timestamp DESC')
    users = c.fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    """Retrieve a specific user profile by ID"""
    if not os.path.exists('users.db'):
        init_db()
        return None
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM user_profiles WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def delete_user(user_id):
    """Delete a user profile by ID"""
    if not os.path.exists('users.db'):
        init_db()
        return False
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_profiles WHERE id = ?', (user_id,))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def update_user(user_id, name, income, expenses, savings, risk_profile):
    """Update an existing user profile"""
    if not os.path.exists('users.db'):
        init_db()
        return False
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        UPDATE user_profiles 
        SET name=?, monthly_income=?, monthly_expenses=?, current_savings=?, risk_profile=?
        WHERE id=?
    ''', (name, income, expenses, savings, risk_profile, user_id))
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Initialize database when module is imported
init_db()