import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "cookies.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cookies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                website TEXT NOT NULL,
                cookie_name TEXT NOT NULL,
                cookie_value TEXT NOT NULL,
                domain TEXT,
                path TEXT DEFAULT '/',
                expires TEXT,
                is_valid BOOLEAN DEFAULT 1,
                last_validated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, website, cookie_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_user(self, username: str, password: str) -> bool:
        """Create a new user"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate user and return user_id if successful"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def save_cookies(self, user_id: int, website: str, cookies: List[Dict]) -> bool:
        """Save cookies for a user and website"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for cookie in cookies:
                cursor.execute('''
                    INSERT OR REPLACE INTO cookies 
                    (user_id, website, cookie_name, cookie_value, domain, path, expires, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    website,
                    cookie.get('name', ''),
                    cookie.get('value', ''),
                    cookie.get('domain', ''),
                    cookie.get('path', '/'),
                    cookie.get('expires', '')
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving cookies: {e}")
            return False
    
    def get_user_cookies(self, user_id: int, website: str = None) -> List[Dict]:
        """Get cookies for a user, optionally filtered by website"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if website:
            cursor.execute('''
                SELECT id, website, cookie_name, cookie_value, domain, path, 
                       expires, is_valid, last_validated, created_at
                FROM cookies 
                WHERE user_id = ? AND website = ?
                ORDER BY created_at DESC
            ''', (user_id, website))
        else:
            cursor.execute('''
                SELECT id, website, cookie_name, cookie_value, domain, path, 
                       expires, is_valid, last_validated, created_at
                FROM cookies 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        cookies = []
        for row in results:
            cookies.append({
                'id': row[0],
                'website': row[1],
                'name': row[2],
                'value': row[3],
                'domain': row[4],
                'path': row[5],
                'expires': row[6],
                'is_valid': row[7],
                'last_validated': row[8],
                'created_at': row[9]
            })
        
        return cookies
    
    def update_cookie_validity(self, cookie_id: int, is_valid: bool) -> bool:
        """Update cookie validity status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE cookies 
                SET is_valid = ?, last_validated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (is_valid, cookie_id))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def delete_cookie(self, user_id: int, cookie_id: int) -> bool:
        """Delete a cookie belonging to the user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cookies WHERE id = ? AND user_id = ?",
                (cookie_id, user_id)
            )
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception:
            return False