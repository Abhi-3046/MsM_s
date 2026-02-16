const API_BASE_URL = 'http://localhost:5000';

function signup() {
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const errorMsg = document.getElementById("errorMsg");

  errorMsg.innerText = "";

  if (!username || !email || !password || !confirmPassword) {
    errorMsg.innerText = "All fields are required.";
    return;
  }

  if (password.length < 6) {
    errorMsg.innerText = "Password must be at least 6 characters.";
    return;
  }

  if (password !== confirmPassword) {
    errorMsg.innerText = "Passwords do not match.";
    return;
  }

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    errorMsg.innerText = "Please enter a valid email address.";
    return;
  }

  // Send signup request to backend
  fetch(`${API_BASE_URL}/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: username,
      email: email,
      password: password
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Store user info in localStorage
      if (data.user) {
        localStorage.setItem('userId', data.user.user_id || data.user.id);
        localStorage.setItem('username', data.user.username);
        localStorage.setItem('userType', 'customer');
      }
      alert("Sign-up successful! Redirecting to login page...");
      window.location.href = 'loginpage.html';
    } else {
      errorMsg.innerText = data.message || "Signup failed. Please try again.";
    }
  })
  .catch(error => {
    console.error('Signup error:', error);
    errorMsg.innerText = "Error connecting to server. Please try again.";
  });
}

function handleGoogleLogin(response) {
  // Handle Google Sign-In response
  console.log('Google Sign-In response:', response);
  
  // Extract credential from response
  const credential = response.credential;
  
  // Send credential to backend for verification
  fetch(`${API_BASE_URL}/google-signin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      credential: credential
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success && data.user) {
      // Store user info in localStorage
      localStorage.setItem('userId', data.user.user_id || data.user.id);
      localStorage.setItem('username', data.user.username || data.user.name);
      localStorage.setItem('userType', 'customer');
      
      alert('Google Sign-In successful!');
      window.location.href = 'index.html';
    } else {
      showError(data.message || 'Google Sign-In failed. Please try again.');
    }
  })
  .catch(error => {
    console.error('Google Sign-In error:', error);
    showError('Error connecting to server. Please try again.');
  });
}

function showError(message) {
  const errorMsg = document.getElementById('errorMsg');
  errorMsg.textContent = message;
  errorMsg.style.display = 'block';
}

// Allow Enter key to submit form
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input');
  inputs.forEach(input => {
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        signup();
      }
    });
  });
});

