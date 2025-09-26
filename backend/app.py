from flask import Flask, request, jsonify, session
from flask_cors import CORS
from backend.models.database import Database
from backend.utils.cookie_validator import CookieValidator
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Enable CORS for frontend-backend separation
CORS(app, supports_credentials=True)

# Initialize database and validator
db = Database()
validator = CookieValidator()

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    success = db.create_user(username, password)
    
    if success:
        return jsonify({'message': 'User registered successfully'}), 201
    else:
        return jsonify({'error': 'Username already exists'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username'].strip()
    password = data['password']
    
    user_id = db.authenticate_user(username, password)
    
    if user_id:
        session['user_id'] = user_id
        session['username'] = username
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user_id,
                'username': username
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/cookies', methods=['POST'])
def upload_cookies():
    """Upload cookies for a website"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('website'):
        return jsonify({'error': 'Website is required'}), 400
    
    website = data['website'].strip()
    cookies_data = data.get('cookies', [])
    cookie_header = data.get('cookie_header', '')
    
    # Parse cookies from different sources
    cookies = []
    
    if cookie_header:
        # Parse from raw cookie header
        cookies.extend(validator.parse_cookies_from_header(cookie_header))
    
    if cookies_data:
        # Parse from JSON cookies array
        for cookie in cookies_data:
            if isinstance(cookie, dict) and cookie.get('name') and cookie.get('value'):
                cookies.append({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie.get('domain', ''),
                    'path': cookie.get('path', '/'),
                    'expires': cookie.get('expires', '')
                })
    
    if not cookies:
        return jsonify({'error': 'No valid cookies provided'}), 400
    
    # Save cookies to database
    success = db.save_cookies(session['user_id'], website, cookies)
    
    if success:
        return jsonify({
            'message': f'Successfully uploaded {len(cookies)} cookies for {website}',
            'count': len(cookies)
        }), 201
    else:
        return jsonify({'error': 'Failed to save cookies'}), 500

@app.route('/api/cookies', methods=['GET'])
def get_cookies():
    """Get user's cookies, optionally filtered by website"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    website = request.args.get('website')
    cookies = db.get_user_cookies(session['user_id'], website)
    
    return jsonify({
        'cookies': cookies,
        'count': len(cookies)
    }), 200

@app.route('/api/cookies/<int:cookie_id>', methods=['DELETE'])
def delete_cookie(cookie_id):
    """Delete a specific cookie"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    success = db.delete_cookie(session['user_id'], cookie_id)
    
    if success:
        return jsonify({'message': 'Cookie deleted successfully'}), 200
    else:
        return jsonify({'error': 'Cookie not found or access denied'}), 404

@app.route('/api/validate', methods=['POST'])
def validate_cookies():
    """Validate cookies for a specific website"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('website'):
        return jsonify({'error': 'Website is required'}), 400
    
    website = data['website'].strip()
    
    # Get cookies for the website
    cookies = db.get_user_cookies(session['user_id'], website)
    
    if not cookies:
        return jsonify({'error': 'No cookies found for this website'}), 404
    
    # Validate cookies
    try:
        validation_results = validator.validate_cookies_for_website(website, cookies)
        
        # Update database with validation results
        valid_count = 0
        invalid_count = 0
        
        for cookie_id, is_valid in validation_results:
            db.update_cookie_validity(cookie_id, is_valid)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        return jsonify({
            'message': f'Validated {len(cookies)} cookies for {website}',
            'results': {
                'total': len(cookies),
                'valid': valid_count,
                'invalid': invalid_count
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@app.route('/api/user', methods=['GET'])
def get_user_info():
    """Get current user information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    return jsonify({
        'user': {
            'id': session['user_id'],
            'username': session['username']
        }
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)