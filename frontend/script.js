// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Global state
let currentUser = null;

// DOM Elements
const authSection = document.getElementById('auth-section');
const mainSection = document.getElementById('main-section');
const usernameSpan = document.getElementById('username');
const loadingDiv = document.getElementById('loading');
const messageDiv = document.getElementById('message');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// Authentication Functions
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value;
    
    if (username.length < 3) {
        showMessage('Username must be at least 3 characters long', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('Password must be at least 6 characters long', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('Registration successful! Please login.', 'success');
            showLogin();
            document.getElementById('register-form').reset();
        } else {
            showMessage(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showMessage('Please enter both username and password', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showMainSection();
            showMessage('Login successful!', 'success');
            document.getElementById('login-form').reset();
        } else {
            showMessage(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function logout() {
    showLoading(true);
    
    try {
        await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        showAuthSection();
        showMessage('Logged out successfully', 'success');
    } catch (error) {
        showMessage('Logout error', 'error');
    } finally {
        showLoading(false);
    }
}

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/user`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showMainSection();
        } else {
            showAuthSection();
        }
    } catch (error) {
        showAuthSection();
    }
}

// UI Functions
function showAuthSection() {
    authSection.style.display = 'block';
    mainSection.style.display = 'none';
}

function showMainSection() {
    authSection.style.display = 'none';
    mainSection.style.display = 'block';
    usernameSpan.textContent = currentUser ? currentUser.username : '';
    loadCookies();
}

function showLoading(show) {
    loadingDiv.style.display = show ? 'flex' : 'none';
}

function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;
    
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 5000);
}

// Cookie Management Functions
function addCookiePair() {
    const container = document.getElementById('cookie-inputs');
    const cookiePair = document.createElement('div');
    cookiePair.className = 'cookie-pair';
    cookiePair.innerHTML = `
        <input type="text" placeholder="Cookie Name" class="cookie-name">
        <input type="text" placeholder="Cookie Value" class="cookie-value">
        <button type="button" onclick="removeCookiePair(this)">Remove</button>
    `;
    container.appendChild(cookiePair);
}

function removeCookiePair(button) {
    const cookiePair = button.parentElement;
    cookiePair.remove();
}

async function uploadCookies(event) {
    event.preventDefault();
    
    const website = document.getElementById('website').value.trim();
    const cookieHeader = document.getElementById('cookie-header').value.trim();
    
    if (!website) {
        showMessage('Please enter a website', 'error');
        return;
    }
    
    // Collect individual cookies
    const cookieInputs = document.querySelectorAll('#cookie-inputs .cookie-pair');
    const cookies = [];
    
    cookieInputs.forEach(pair => {
        const name = pair.querySelector('.cookie-name').value.trim();
        const value = pair.querySelector('.cookie-value').value.trim();
        
        if (name && value) {
            cookies.push({ name, value });
        }
    });
    
    if (!cookieHeader && cookies.length === 0) {
        showMessage('Please provide cookies either via header or individual inputs', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/cookies`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                website,
                cookie_header: cookieHeader,
                cookies
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(data.message, 'success');
            document.querySelector('form').reset();
            // Reset cookie inputs to just one pair
            const container = document.getElementById('cookie-inputs');
            container.innerHTML = `
                <div class="cookie-pair">
                    <input type="text" placeholder="Cookie Name" class="cookie-name">
                    <input type="text" placeholder="Cookie Value" class="cookie-value">
                    <button type="button" onclick="removeCookiePair(this)">Remove</button>
                </div>
            `;
            loadCookies();
        } else {
            showMessage(data.error || 'Failed to upload cookies', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadCookies() {
    const website = document.getElementById('filter-website').value.trim();
    const url = website ? `${API_BASE_URL}/cookies?website=${encodeURIComponent(website)}` : `${API_BASE_URL}/cookies`;
    
    try {
        const response = await fetch(url, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayCookies(data.cookies);
        } else {
            showMessage(data.error || 'Failed to load cookies', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    }
}

function displayCookies(cookies) {
    const container = document.getElementById('cookies-list');
    
    if (cookies.length === 0) {
        container.innerHTML = '<p>No cookies found. Upload some cookies first.</p>';
        return;
    }
    
    // Group cookies by website
    const groupedCookies = {};
    cookies.forEach(cookie => {
        if (!groupedCookies[cookie.website]) {
            groupedCookies[cookie.website] = [];
        }
        groupedCookies[cookie.website].push(cookie);
    });
    
    let html = '';
    
    Object.keys(groupedCookies).forEach(website => {
        const siteCookies = groupedCookies[website];
        
        html += `<div class="website-group">`;
        html += `<div class="cookie-item">`;
        html += `<div class="cookie-header">`;
        html += `<div class="cookie-website">${website}</div>`;
        html += `<div class="cookie-status">`;
        html += `<button class="btn-validate" onclick="validateWebsiteCookies('${website}')">Validate All</button>`;
        html += `</div>`;
        html += `</div>`;
        
        siteCookies.forEach(cookie => {
            const statusClass = cookie.is_valid === null ? 'unknown' : 
                               cookie.is_valid ? 'valid' : 'invalid';
            const statusText = cookie.is_valid === null ? 'Not validated' :
                              cookie.is_valid ? 'Valid' : 'Invalid';
            
            html += `<div class="cookie-details">`;
            html += `<strong>${cookie.name}</strong>`;
            html += `<span>${cookie.value}</span>`;
            html += `</div>`;
            
            html += `<div class="cookie-details">`;
            html += `<span>Status:</span>`;
            html += `<span class="status-badge status-${statusClass}">${statusText}</span>`;
            html += `</div>`;
            
            if (cookie.last_validated) {
                html += `<div class="cookie-details">`;
                html += `<span>Last validated:</span>`;
                html += `<span>${new Date(cookie.last_validated).toLocaleString()}</span>`;
                html += `</div>`;
            }
            
            html += `<div class="cookie-actions">`;
            html += `<button class="btn-delete" onclick="deleteCookie(${cookie.id})">Delete</button>`;
            html += `</div>`;
            html += `<hr style="margin: 10px 0; border: none; border-top: 1px solid #eee;">`;
        });
        
        html += `</div></div>`;
    });
    
    container.innerHTML = html;
}

async function validateWebsiteCookies(website) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ website }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(data.message, 'success');
            loadCookies(); // Refresh the display
        } else {
            showMessage(data.error || 'Validation failed', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteCookie(cookieId) {
    if (!confirm('Are you sure you want to delete this cookie?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/cookies/${cookieId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('Cookie deleted successfully', 'success');
            loadCookies(); // Refresh the display
        } else {
            showMessage(data.error || 'Failed to delete cookie', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function clearFilter() {
    document.getElementById('filter-website').value = '';
    loadCookies();
}