# ✅ Setup Checklist - Multi-User HealthApp

Copy this checklist and check off items as you complete them.

---

## Phase 1: Firebase Setup (15 minutes)

### Create Project
- [ ] Go to https://console.firebase.google.com
- [ ] Click "Add project" or "Create a project"
- [ ] Name: `HealthApp` (or your choice)
- [ ] Disable Google Analytics (optional)
- [ ] Click "Create project"
- [ ] Wait ~30 seconds
- [ ] Click "Continue"

### Enable Authentication
- [ ] Click "Authentication" in left sidebar
- [ ] Click "Get started"
- [ ] Click "Sign-in method" tab
- [ ] Click "Email/Password"
- [ ] Toggle "Enable" ON
- [ ] Click "Save"
- [ ] Click "Google"
- [ ] Toggle "Enable" ON
- [ ] Select support email
- [ ] Click "Save"

### Enable Firestore
- [ ] Click "Firestore Database" in left sidebar
- [ ] Click "Create database"
- [ ] Select "Start in test mode"
- [ ] Click "Next"
- [ ] Choose location: `us-central` (or nearest)
- [ ] Click "Enable"
- [ ] Wait ~1 minute

### Update Security Rules
- [ ] Click "Rules" tab in Firestore
- [ ] Replace rules with code from FIREBASE_SETUP.md Step 3.3
- [ ] Click "Publish"

### Get Configuration
- [ ] Click ⚙️ "Project settings" (gear icon)
- [ ] Scroll to "Your apps"
- [ ] Click `</>` (web icon)
- [ ] App nickname: `HealthApp Web`
- [ ] Hosting: UNCHECKED
- [ ] Click "Register app"
- [ ] Copy the `firebaseConfig` object

### Update Your App
- [ ] Open: `c:\Users\Sdela\vcodeprojects\HealthApp\web\firebase-config.js`
- [ ] Replace placeholder values with YOUR config
- [ ] Save file

---

## Phase 2: Local Testing (5 minutes)

### Start Server
- [ ] Open PowerShell in VS Code
- [ ] Run: `cd c:\Users\Sdela\vcodeprojects\HealthApp\web`
- [ ] Run: `python -m http.server 8000`
- [ ] Leave terminal running

### Test Authentication
- [ ] Open browser: http://localhost:8000/auth.html
- [ ] Click "Sign Up" link
- [ ] Enter email: `test@example.com`
- [ ] Enter password: `test123`
- [ ] Click "Sign Up"
- [ ] Should redirect to main app
- [ ] Verify email shows in top-right corner

### Test Data Sync
- [ ] Add a recipe to Monday
- [ ] Click "Save Plan"
- [ ] Should see "saved to cloud" message
- [ ] Go to biomarkers tab
- [ ] Enter Vitamin D: `35`
- [ ] Click "Analyze & Get Recommendations"
- [ ] Click "Save Results"
- [ ] Should see "saved to cloud" message

### Verify Data in Firebase
- [ ] Go back to Firebase Console
- [ ] Click "Firestore Database"
- [ ] Should see `users` collection
- [ ] Click your user ID
- [ ] Should see `mealPlans` and `biomarkers` subcollections
- [ ] Data should match what you entered

### Test Logout/Login
- [ ] Click user email in top-right
- [ ] Click "Logout"
- [ ] Should redirect to auth.html
- [ ] Login again with same email
- [ ] Data should still be there (synced from cloud)

---

## Phase 3: GitHub Deployment (15 minutes)

### Create Repository
- [ ] Go to: https://github.com/new
- [ ] Repository name: `HealthApp`
- [ ] Public or Private: Your choice
- [ ] DON'T initialize with README
- [ ] Click "Create repository"

### Prepare for Git
- [ ] In PowerShell: `cd c:\Users\Sdela\vcodeprojects\HealthApp`
- [ ] Run: `git init`
- [ ] Run: `git add .`
- [ ] Run: `git commit -m "Multi-user HealthApp with Firebase"`

### Push to GitHub
Replace `YOUR_USERNAME` with your GitHub username:
- [ ] Run: `git branch -M main`
- [ ] Run: `git remote add origin https://github.com/YOUR_USERNAME/HealthApp.git`
- [ ] Run: `git push -u origin main`
- [ ] Verify files appear on GitHub

### Enable GitHub Pages
- [ ] Go to your GitHub repository
- [ ] Click "Settings" tab
- [ ] Click "Pages" from left sidebar
- [ ] Source: Select `main` branch
- [ ] Folder: Select `/` (root)
- [ ] Click "Save"
- [ ] Wait 2-5 minutes for deployment
- [ ] Copy the URL (e.g., `https://YOUR_USERNAME.github.io/HealthApp/`)

### Test Live App
- [ ] Visit: `https://YOUR_USERNAME.github.io/HealthApp/web/auth.html`
- [ ] Should see login page
- [ ] Try to sign up → Will get error (domain not authorized yet)

### Add Authorized Domain
- [ ] Back to Firebase Console
- [ ] Click "Authentication"
- [ ] Click "Settings" tab
- [ ] Scroll to "Authorized domains"
- [ ] Click "Add domain"
- [ ] Enter: `YOUR_USERNAME.github.io` (NO https://, NO path)
- [ ] Click "Add"

### Final Test
- [ ] Refresh your live app URL
- [ ] Sign up with NEW email (e.g., `real@example.com`)
- [ ] Should work now!
- [ ] Test all features
- [ ] Try logging in from phone

---

## Phase 4: Share & Use (Ongoing)

### Share with Others
- [ ] Share link: `https://YOUR_USERNAME.github.io/HealthApp/web/auth.html`
- [ ] Each person creates their own account
- [ ] Everyone has private data

### Use the App
- [ ] Plan your weekly meals
- [ ] Track nutrition
- [ ] Enter Function Health biomarkers
- [ ] Get personalized recommendations
- [ ] Everything syncs across devices!

---

## Verification Checklist

After completing all phases:

### Authentication Works
- [ ] Can sign up with email
- [ ] Can login with email
- [ ] Can sign in with Google
- [ ] Can logout
- [ ] Email shows in user menu

### Data Persists
- [ ] Meal plan saves to cloud
- [ ] Biomarkers save to cloud
- [ ] Data loads after refresh
- [ ] Data syncs across devices

### Security
- [ ] Each user has separate data
- [ ] Can't see other users' data
- [ ] Firestore rules are published
- [ ] Authorized domains configured

### Deployment
- [ ] App accessible at GitHub Pages URL
- [ ] Works on desktop
- [ ] Works on mobile
- [ ] HTTPS enabled (automatic)

---

## Common Issues & Fixes

### ❌ "Firebase not defined" error
✅ Update `firebase-config.js` with real config from Firebase Console

### ❌ "Redirect loop" at auth.html
✅ Add your domain to Firebase → Authentication → Authorized domains

### ❌ "Permission denied" when saving
✅ Publish security rules in Firestore (FIREBASE_SETUP.md Step 3.3)

### ❌ GitHub Pages shows 404
✅ Wait 5-10 minutes, then hard refresh (Ctrl+Shift+R)

### ❌ Google sign-in fails
✅ Verify Google is enabled in Firebase → Authentication → Sign-in method

---

## Success! 🎉

When all items are checked:
✅ Multi-user app is live
✅ Free hosting forever
✅ Secure authentication
✅ Cloud data sync
✅ Accessible worldwide
✅ Works on all devices

**Your HealthApp is production-ready!**

Share this checklist URL with anyone else deploying the app.
