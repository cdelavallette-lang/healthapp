# Firebase & GitHub Pages Setup Guide
## Multi-User HealthApp Deployment

---

## Step 1: Create Firebase Project (5 minutes)

### 1.1 Go to Firebase Console
- Visit: https://console.firebase.google.com/
- Click **"Add project"** or **"Create a project"**

### 1.2 Create Project
- **Project name**: `HealthApp` (or any name you prefer)
- Click **Continue**
- **Google Analytics**: Toggle OFF (optional for this app)
- Click **Create project**
- Wait ~30 seconds for setup to complete
- Click **Continue**

---

## Step 2: Setup Firebase Authentication (3 minutes)

### 2.1 Enable Authentication
- In Firebase Console, click **"Authentication"** from left sidebar
- Click **"Get started"**

### 2.2 Enable Email/Password Authentication
- Click **"Sign-in method"** tab
- Click **"Email/Password"** from the list
- Toggle **"Enable"** switch ON
- Click **"Save"**

### 2.3 Enable Google Sign-In (Optional)
- Still in "Sign-in method" tab
- Click **"Google"** from the list
- Toggle **"Enable"** switch ON
- Select your support email from dropdown
- Click **"Save"**

---

## Step 3: Setup Firestore Database (2 minutes)

### 3.1 Create Database
- Click **"Firestore Database"** from left sidebar
- Click **"Create database"**

### 3.2 Configure Security Rules
- Select **"Start in test mode"** (we'll update security later)
- Click **"Next"**
- Choose location: **us-central** (or closest to you)
- Click **"Enable"**
- Wait ~1 minute for database creation

### 3.3 Update Security Rules (Important!)
- Once database is ready, click **"Rules"** tab
- Replace the default rules with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      // User's subcollections (meal plans, biomarkers)
      match /{document=**} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

- Click **"Publish"**

---

## Step 4: Get Firebase Configuration (2 minutes)

### 4.1 Register Web App
- In Firebase Console, click ⚙️ **"Project settings"** (gear icon)
- Scroll to **"Your apps"** section
- Click the **</>** (web) icon
- **App nickname**: `HealthApp Web`
- **Firebase Hosting**: Leave UNCHECKED (we're using GitHub Pages)
- Click **"Register app"**

### 4.2 Copy Configuration
You'll see something like:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyD3x...",
  authDomain: "healthapp-12345.firebaseapp.com",
  projectId: "healthapp-12345",
  storageBucket: "healthapp-12345.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

### 4.3 Update Your Config File
- Open: `c:\Users\Sdela\vcodeprojects\HealthApp\web\firebase-config.js`
- Replace the placeholder values with YOUR actual Firebase config
- **Save the file**

---

## Step 5: Test Locally (2 minutes)

### 5.1 Start Local Server
- Open PowerShell in VS Code
- Run:
```powershell
cd c:\Users\Sdela\vcodeprojects\HealthApp\web
python -m http.server 8000
```

### 5.2 Test Authentication
- Open browser: http://localhost:8000/auth.html
- Click **"Sign Up"** link
- Enter email: `test@example.com`
- Password: `test123` (minimum 6 characters)
- Click **"Sign Up"**
- Should redirect to main app with your email in top-right

### 5.3 Test Data Sync
- Add a recipe to meal plan
- Click **"Save Plan"**
- Enter some biomarkers
- Click **"Save Results"**
- Open browser console (F12) - should see "saved successfully" messages
- Refresh page - data should persist

---

## Step 6: Deploy to GitHub Pages (10 minutes)

### 6.1 Create GitHub Repository
- Go to: https://github.com/new
- **Repository name**: `HealthApp`
- **Public** or **Private**: Your choice (both work with Pages)
- **DON'T** initialize with README
- Click **"Create repository"**

### 6.2 Prepare Files for Deployment
In PowerShell:
```powershell
cd c:\Users\Sdela\vcodeprojects\HealthApp

# Initialize git
git init

# Create .gitignore
@"
*.pyc
__pycache__/
.env
.vscode/
"@ | Out-File -FilePath .gitignore -Encoding utf8

# Stage files
git add .
git commit -m "Initial commit: Multi-user HealthApp with Firebase"
```

### 6.3 Push to GitHub
Replace `YOUR_USERNAME` with your GitHub username:
```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/HealthApp.git
git push -u origin main
```

### 6.4 Enable GitHub Pages
- Go to your GitHub repository
- Click **"Settings"** tab
- Click **"Pages"** from left sidebar
- **Source**: Select `main` branch
- **Folder**: Select `/web` (if option available) OR `/root`
- Click **"Save"**
- Wait ~2 minutes for deployment

### 6.5 Get Your Live URL
- Your app will be live at: `https://YOUR_USERNAME.github.io/HealthApp/web/auth.html`
- (If you set folder to `/root`, the path will be different)

---

## Step 7: Update Firebase Auth Domain (1 minute)

### 7.1 Add GitHub Pages Domain
- Back in Firebase Console → **Authentication**
- Click **"Settings"** tab
- Scroll to **"Authorized domains"**
- Click **"Add domain"**
- Enter: `YOUR_USERNAME.github.io`
- Click **"Add"**

---

## Step 8: Test Live App

### 8.1 Visit Your Live URL
- Open: `https://YOUR_USERNAME.github.io/HealthApp/web/auth.html`
- Create new account
- Test all features
- Verify data syncs across devices by logging in from phone/different computer

---

## Step 9: Optional Enhancements

### 9.1 Custom Domain (Optional)
If you own a domain:
- In GitHub repo Settings → Pages
- Add custom domain
- Update Firebase authorized domains

### 9.2 Progressive Web App (PWA)
Add to `web/` folder:
- `manifest.json` for installability
- Service worker for offline support

### 9.3 Improved Security Rules
Update Firestore rules for production:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow create: if request.auth != null && request.auth.uid == userId;
      allow read, update, delete: if request.auth != null && request.auth.uid == userId;
      
      match /mealPlans/{planId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      
      match /biomarkers/{markerId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

---

## Troubleshooting

### "Firebase not defined" error
- Make sure Firebase scripts load BEFORE `firebase-config.js`
- Check browser console for script loading errors

### Authentication redirect loop
- Verify `authDomain` in `firebase-config.js` matches Firebase console
- Check that domain is in Firebase authorized domains list

### Data not saving
- Open browser console (F12) → Network tab
- Look for Firestore errors (red requests)
- Check Firestore security rules allow writes

### GitHub Pages 404 error
- Wait 5-10 minutes after enabling Pages (initial deployment)
- Check repository is public OR you have GitHub Pro (for private repo Pages)
- Verify file paths are correct (case-sensitive!)

---

## Cost Breakdown

### Firebase Free Tier (Spark Plan)
- **Authentication**: 50,000 users/month
- **Firestore**: 
  - 50,000 reads/day
  - 20,000 writes/day
  - 1 GB storage
- **Should last**: Years at personal/small business scale

### GitHub Pages
- **Completely free** for public repos
- **Free** for private repos with GitHub Pro (free for students)
- **Bandwidth**: 100 GB/month
- **Build minutes**: 2,000/month

### When You'll Need to Pay
- **Firebase**: If you exceed ~10 active users with heavy usage (~$5-10/month on Blaze plan)
- **GitHub**: Never for this use case

---

## What You've Accomplished ✅

1. ✅ Multi-user authentication (email/password + Google)
2. ✅ Cloud data storage per user (meal plans, biomarkers, preferences)
3. ✅ Cross-device sync (login from anywhere)
4. ✅ Secure data isolation (users can't see others' data)
5. ✅ Live web app accessible worldwide
6. ✅ Zero hosting costs
7. ✅ Automatic HTTPS
8. ✅ Scalable to hundreds of users

Your HealthApp is now production-ready! 🎉
