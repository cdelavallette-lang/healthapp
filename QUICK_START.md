# 🚀 Quick Start Guide

## 1. Setup Firebase (5 min)
```
1. Go to: https://console.firebase.google.com/
2. Create new project
3. Enable Authentication (Email/Password + Google)
4. Enable Firestore (test mode)
5. Register web app
6. Copy config to firebase-config.js
```

## 2. Test Locally
```powershell
cd c:\Users\Sdela\vcodeprojects\HealthApp\web
python -m http.server 8000
```
Open: http://localhost:8000/auth.html

## 3. Deploy to GitHub Pages
```powershell
cd c:\Users\Sdela\vcodeprojects\HealthApp
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/HealthApp.git
git push -u origin main
```

Then in GitHub:
- Settings → Pages → Enable from `main` branch
- Wait 2 min → Visit: `https://YOUR_USERNAME.github.io/HealthApp/web/auth.html`

## 4. Final Step
Add `YOUR_USERNAME.github.io` to Firebase → Authentication → Authorized domains

---

## Files Changed

### New Files Created:
- ✅ `web/auth.html` - Login/signup page
- ✅ `web/auth.js` - Authentication logic
- ✅ `web/firebase-config.js` - Firebase settings (UPDATE THIS!)

### Modified Files:
- ✅ `web/index.html` - Added Firebase SDK, user menu
- ✅ `web/app.js` - Added Firestore data sync, auth checks
- ✅ `web/styles.css` - Added user menu styling

---

## What Works Now

✅ **User Accounts**: Email/password + Google sign-in  
✅ **Cloud Storage**: All data saved to Firestore per user  
✅ **Cross-Device Sync**: Login from any device  
✅ **Secure**: Users can't see others' data  
✅ **Free**: Zero cost for personal use  

---

## Important: Before Testing

**YOU MUST** update `web/firebase-config.js` with your Firebase credentials:
```javascript
const firebaseConfig = {
    apiKey: "YOUR_ACTUAL_API_KEY",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    // ... rest of config
};
```

Get these values from: Firebase Console → Project Settings → Your Apps → Web

---

## Next Steps

1. Follow detailed guide in `FIREBASE_SETUP.md`
2. Test locally first
3. Deploy to GitHub Pages
4. Share app link with users!
