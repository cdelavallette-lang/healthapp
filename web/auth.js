// Authentication Logic for Login/Signup Page

let isSignUpMode = false;

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    auth.onAuthStateChanged((user) => {
        if (user) {
            // User is signed in, redirect to main app
            window.location.href = 'index.html';
        }
    });
    
    setupAuthEventListeners();
});

function setupAuthEventListeners() {
    const authForm = document.getElementById('auth-form');
    const authSwitchLink = document.getElementById('auth-switch-link');
    const googleSignInBtn = document.getElementById('google-signin-btn');
    
    // Handle form submission
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (isSignUpMode) {
            const confirmPassword = document.getElementById('confirm-password').value;
            if (password !== confirmPassword) {
                showError('Passwords do not match');
                return;
            }
            await signUp(email, password);
        } else {
            await signIn(email, password);
        }
    });
    
    // Toggle between sign in and sign up
    authSwitchLink.addEventListener('click', (e) => {
        e.preventDefault();
        toggleAuthMode();
    });
    
    // Google sign in
    googleSignInBtn.addEventListener('click', async () => {
        await signInWithGoogle();
    });
}

function toggleAuthMode() {
    isSignUpMode = !isSignUpMode;
    
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const authSubmitBtn = document.getElementById('auth-submit-btn');
    const authSwitchText = document.getElementById('auth-switch-text');
    const authSwitchLink = document.getElementById('auth-switch-link');
    const confirmPasswordGroup = document.getElementById('confirm-password-group');
    
    if (isSignUpMode) {
        authTitle.textContent = 'Create Account';
        authSubtitle.textContent = 'Start planning healthy meals today';
        authSubmitBtn.textContent = 'Sign Up';
        authSwitchText.textContent = 'Already have an account?';
        authSwitchLink.textContent = 'Sign In';
        confirmPasswordGroup.style.display = 'flex';
        document.getElementById('confirm-password').required = true;
    } else {
        authTitle.textContent = 'Welcome Back';
        authSubtitle.textContent = 'Sign in to access your meal plans';
        authSubmitBtn.textContent = 'Sign In';
        authSwitchText.textContent = "Don't have an account?";
        authSwitchLink.textContent = 'Sign Up';
        confirmPasswordGroup.style.display = 'none';
        document.getElementById('confirm-password').required = false;
    }
    
    hideError();
}

async function signUp(email, password) {
    try {
        showLoading();
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Create user profile in Firestore
        await db.collection('users').doc(user.uid).set({
            email: user.email,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
            preferences: {
                servings: 4,
                theme: 'light'
            }
        });
        
        console.log('User created successfully:', user.uid);
        // Redirect handled by onAuthStateChanged
    } catch (error) {
        hideLoading();
        handleAuthError(error);
    }
}

async function signIn(email, password) {
    try {
        showLoading();
        await auth.signInWithEmailAndPassword(email, password);
        console.log('User signed in successfully');
        // Redirect handled by onAuthStateChanged
    } catch (error) {
        hideLoading();
        handleAuthError(error);
    }
}

async function signInWithGoogle() {
    try {
        showLoading();
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await auth.signInWithPopup(provider);
        const user = result.user;
        
        // Check if new user and create profile
        const userDoc = await db.collection('users').doc(user.uid).get();
        if (!userDoc.exists) {
            await db.collection('users').doc(user.uid).set({
                email: user.email,
                displayName: user.displayName,
                photoURL: user.photoURL,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                preferences: {
                    servings: 4,
                    theme: 'light'
                }
            });
        }
        
        console.log('Google sign in successful');
        // Redirect handled by onAuthStateChanged
    } catch (error) {
        hideLoading();
        handleAuthError(error);
    }
}

function handleAuthError(error) {
    console.error('Authentication error:', error);
    
    let message = 'An error occurred. Please try again.';
    
    switch (error.code) {
        case 'auth/email-already-in-use':
            message = 'This email is already registered. Please sign in instead.';
            break;
        case 'auth/invalid-email':
            message = 'Invalid email address.';
            break;
        case 'auth/weak-password':
            message = 'Password must be at least 6 characters.';
            break;
        case 'auth/user-not-found':
            message = 'No account found with this email.';
            break;
        case 'auth/wrong-password':
            message = 'Incorrect password.';
            break;
        case 'auth/popup-closed-by-user':
            message = 'Sign in cancelled.';
            break;
        case 'auth/network-request-failed':
            message = 'Network error. Please check your connection.';
            break;
    }
    
    showError(message);
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}

function hideError() {
    const errorDiv = document.getElementById('error-message');
    errorDiv.classList.remove('show');
}

function showLoading() {
    const submitBtn = document.getElementById('auth-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Loading...';
}

function hideLoading() {
    const submitBtn = document.getElementById('auth-submit-btn');
    submitBtn.disabled = false;
    submitBtn.textContent = isSignUpMode ? 'Sign Up' : 'Sign In';
}
