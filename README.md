# Cookie Management System

A web-based cookie management system that allows users to upload, manage, and validate website cookies. The system features a frontend-backend separation architecture.

## Features

- **User Authentication**: Register and login functionality
- **Cookie Upload**: Upload cookies via raw cookie headers or individual cookie pairs
- **Cookie Management**: View, filter, and delete cookies by website
- **Cookie Validation**: Test cookie validity by making requests to the target website
- **Real-time Status**: Track cookie validity and last validation time

## Architecture

### Backend (Flask)
- `backend/app.py` - Main Flask application with API endpoints
- `backend/models/database.py` - SQLite database models and operations
- `backend/utils/cookie_validator.py` - Cookie validation logic

### Frontend (HTML/CSS/JavaScript)
- `frontend/index.html` - Main web interface
- `frontend/style.css` - Responsive styling
- `frontend/script.js` - Client-side functionality

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
cd backend
python app.py
```

3. Open the frontend:
Open `frontend/index.html` in your web browser, or serve it with a local HTTP server:
```bash
cd frontend
python -m http.server 8000
```

## Usage

1. **Register/Login**: Create an account or login with existing credentials
2. **Upload Cookies**: 
   - Enter the website URL
   - Paste raw cookie header OR enter individual cookie name-value pairs
   - Submit to save cookies to your account
3. **Manage Cookies**: View all your cookies, filter by website
4. **Validate Cookies**: Test if cookies are still valid by clicking "Validate All"
5. **Delete Cookies**: Remove unwanted cookies from your collection

## API Endpoints

- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout
- `GET /api/user` - Get current user info
- `POST /api/cookies` - Upload cookies
- `GET /api/cookies` - Get user cookies (optional website filter)
- `DELETE /api/cookies/<id>` - Delete specific cookie
- `POST /api/validate` - Validate cookies for a website
- `GET /api/health` - Health check

## Security Features

- Password hashing using SHA-256
- Session-based authentication
- CORS enabled for frontend-backend separation
- User isolation (users can only access their own cookies)

## Database Schema

### Users Table
- id (Primary Key)
- username (Unique)
- password_hash
- created_at

### Cookies Table
- id (Primary Key)
- user_id (Foreign Key)
- website
- cookie_name
- cookie_value
- domain
- path
- expires
- is_valid
- last_validated
- created_at