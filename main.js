// Main JavaScript for FraudShield System

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status
    const isAuthenticated = localStorage.getItem('auth_token') !== null;
    
    // Update navigation based on authentication status
    updateNavigation(isAuthenticated);
    
    // Handle Upload page authentication requirement
    const isUploadPage = window.location.pathname.includes('upload.html');
    if (isUploadPage && !isAuthenticated) {
        // Replace upload form with authentication required message
        const container = document.querySelector('.container');
        if (container) {
            const originalContent = container.innerHTML;
            container.innerHTML = `
                <div class="auth-required">
                    <h2><i class="fas fa-lock"></i> Authentication Required</h2>
                    <p>You need to sign in or sign up to upload and analyze transactions.</p>
                    <div class="auth-buttons">
                        <a href="login.html" class="btn-primary">Login</a>
                        <a href="signup.html" class="btn-secondary">Sign Up</a>
                    </div>
                </div>
            `;
        }
    }
    
    // Function to update navigation based on authentication status
    function updateNavigation(isLoggedIn) {
        const navButtons = document.querySelector('.nav-buttons');
        if (navButtons) {
            // Get sign up button
            const signupButton = navButtons.querySelector('a[href="signup.html"]');
            // Create logout button element
            const logoutButton = document.createElement('a');
            logoutButton.setAttribute('href', '#');
            logoutButton.className = 'nav-button logout-button';
            logoutButton.innerHTML = 'Logout';
            
            if (isLoggedIn) {
                // If user is logged in, hide signup button and add logout button
                if (signupButton) {
                    signupButton.style.display = 'none';
                }
                
                // Check if logout button already exists, if not add it
                if (!navButtons.querySelector('.logout-button')) {
                    navButtons.appendChild(logoutButton);
                }
                
                // Add event listener to logout button
                logoutButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    logout();
                });
            } else {
                // If user is not logged in, show signup button and remove logout button
                if (signupButton) {
                    signupButton.style.display = 'inline-flex';
                }
                
                // Remove logout button if it exists
                const existingLogoutButton = navButtons.querySelector('.logout-button');
                if (existingLogoutButton) {
                    navButtons.removeChild(existingLogoutButton);
                }
            }
        }
    }
    
    // Logout function
    function logout() {
        // Clear authentication data
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_email');
        localStorage.removeItem('user_name');
        
        // Show feedback message
        showAlert('You have been logged out successfully', 'success');
        
        // Update navigation
        updateNavigation(false);
        
        // Redirect to home page
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);
    }
    
    // Utility Functions
    function showAlert(message, type = 'error') {
        // Find the nearest form or container for feedback
        const alertContainer = document.querySelector('.form-container, .upload-container, .auth-card, .login-card, .container');
        if (alertContainer) {
            // Create or find existing alert element
            let alertElement = alertContainer.querySelector('.alert-message');
            if (!alertElement) {
                alertElement = document.createElement('div');
                alertElement.className = 'alert-message';
                alertContainer.insertBefore(alertElement, alertContainer.firstChild);
            }

            // Set alert content and style
            alertElement.textContent = message;
            alertElement.className = `alert-message ${type === 'success' ? 'success' : 'error'}`;
            alertElement.style.display = 'block';

            // Hide alert after 5 seconds
            setTimeout(() => {
                alertElement.style.display = 'none';
            }, 5000);
        }
    }

    // Email validation function
    function validateEmail(email) {
        const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return re.test(String(email).toLowerCase());
    }

    // Password strength validation
    function validatePassword(password) {
        // At least 8 characters, one uppercase, one lowercase, one number
        const strongRegex = new RegExp("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.{8,})");
        return strongRegex.test(password);
    }

    // Generate OTP function
    function generateOTP() {
        // Generate a 6-digit OTP
        return Math.floor(100000 + Math.random() * 900000).toString();
    }

    // Function to check if user is registered
    function isUserRegistered(email) {
        // Get registered users from localStorage
        const registeredUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
        return registeredUsers.some(user => user.email === email);
    }

    // Function to get user data
    function getUserData(email) {
        const registeredUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
        return registeredUsers.find(user => user.email === email);
    }

    // Login Form Handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            
            // Validation
            if (!email || !validateEmail(email)) {
                showAlert('Please enter a valid email address');
                return;
            }
            
            if (!password) {
                showAlert('Please enter your password');
                return;
            }
            
            // Check if user is registered
            if (!isUserRegistered(email)) {
                showAlert('Account not found. Please register first.');
                setTimeout(() => {
                    window.location.href = 'signup.html';
                }, 2000);
                return;
            }
            
            // Check password
            const userData = getUserData(email);
            if (userData.password !== password) {
                showAlert('Incorrect password. Please try again.');
                return;
            }
            
            // Show OTP verification form
            const otpContainer = document.getElementById('otp-container');
            const originalForm = document.getElementById('login-form');
            
            if (otpContainer && originalForm) {
                // Hide the original form
                originalForm.style.display = 'none';
                
                // Show the OTP container
                otpContainer.style.display = 'block';
                
                // Generate and store OTP
                const otp = generateOTP();
                sessionStorage.setItem('current_otp', otp);
                sessionStorage.setItem('pending_login_email', email);
                
                // In a real system, this would be sent via email or SMS
                // For demo purposes, we'll display it in console and alert
                console.log('Your OTP is:', otp);
                alert(`Your OTP is: ${otp} (In a real system, this would be sent to your email or phone)`);
            }
        });
    }

    // OTP Verification Form Handler
    const otpForm = document.getElementById('otp-form');
    if (otpForm) {
        otpForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const enteredOtp = document.getElementById('otp-input').value.trim();
            const storedOtp = sessionStorage.getItem('current_otp');
            const email = sessionStorage.getItem('pending_login_email');
            
            if (!enteredOtp) {
                showAlert('Please enter the OTP');
                return;
            }
            
            if (enteredOtp !== storedOtp) {
                showAlert('Invalid OTP. Please try again.');
                return;
            }
            
            // OTP is correct, complete login
            showAlert('Login successful! Redirecting...', 'success');
            
            // Store user info for dashboard
            localStorage.setItem('auth_token', 'debug_token');
            localStorage.setItem('user_email', email);
            localStorage.setItem('user_name', email.split('@')[0]);
            
            // Clean up session data
            sessionStorage.removeItem('current_otp');
            sessionStorage.removeItem('pending_login_email');
            
            // Update navigation immediately
            updateNavigation(true);
            
            setTimeout(() => {
                // Redirect to upload page if coming from there, otherwise to index
                const redirectUrl = sessionStorage.getItem('redirect_after_login') || 'index.html';
                sessionStorage.removeItem('redirect_after_login');
                window.location.href = redirectUrl;
            }, 1500);
        });
    }

    // Signup Form Handler
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            // Validation
            if (!email || !validateEmail(email)) {
                showAlert('Please enter a valid email address');
                return;
            }
            
            if (!password) {
                showAlert('Please create a password');
                return;
            }
            
            if (!validatePassword(password)) {
                showAlert('Password must be at least 8 characters with uppercase, lowercase, and number');
                return;
            }
            
            if (password !== confirmPassword) {
                showAlert('Passwords do not match');
                return;
            }
            
            // Check if user already exists
            if (isUserRegistered(email)) {
                showAlert('Email already registered. Please login instead.');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
                return;
            }
            
            // Save user data
            const newUser = {
                email: email,
                password: password,
                registeredOn: new Date().toISOString()
            };
            
            // Get existing users and add new user
            const existingUsers = JSON.parse(localStorage.getItem('registered_users') || '[]');
            existingUsers.push(newUser);
            localStorage.setItem('registered_users', JSON.stringify(existingUsers));
            
            // Show success message
            showAlert('Account created successfully! Redirecting to login...', 'success');
            
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        });
    }

    // Upload Form Handler
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm && isAuthenticated) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileUpload');
            
            // Validate file selection
            if (!fileInput.files || fileInput.files.length === 0) {
                showAlert('Please select a CSV file to upload');
                return;
            }
            
            const file = fileInput.files[0];
            
            // Validate file type
            if (file.type !== 'text/csv' && !file.name.toLowerCase().endsWith('.csv')) {
                showAlert('Please upload a valid CSV file');
                return;
            }
            
            // Validate file size (10MB limit)
            const maxFileSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxFileSize) {
                showAlert('File size exceeds 10MB limit');
                return;
            }
            
            // Simulate file processing
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            
            setTimeout(() => {
                // Restore button state
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-search"></i> Upload & Detect Fraud';
                
                // Show success message
                showAlert('File processed successfully!', 'success');
            }, 2000);
        });
    }

    // "Login to Upload" button handler
    const loginToUploadBtn = document.querySelector('.auth-required .btn-primary');
    if (loginToUploadBtn) {
        loginToUploadBtn.addEventListener('click', function(e) {
            // Store the current page as redirect target after login
            sessionStorage.setItem('redirect_after_login', window.location.href);
        });
    }

    // Add active class to current navigation item
    const currentPage = window.location.pathname.split('/').pop();
    const navButtons = document.querySelectorAll('.nav-button');
    navButtons.forEach(button => {
        const buttonHref = button.getAttribute('href');
        if (buttonHref === currentPage) {
            button.classList.add('active');
        }
    });
});