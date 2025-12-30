# 🥗 HealthApp - Multi-User Meal Planning & Nutrition Optimization

A comprehensive web application for meal planning, biomarker tracking, and personalized nutrition recommendations with multi-user support.

## 🌟 Features

### Core Functionality
- **Recipe Library** - 30+ whole-food recipes with complete nutrition data
- **Weekly Meal Planner** - Drag-and-drop interface for meal scheduling (1-6 servings)
- **Nutrition Analysis** - Real-time nutrient tracking with RDA percentages
- **Biomarker Integration** - Function Health lab results tracking with personalized recommendations

### Advanced Features
- **Bioavailability Calculator** - Adjusts nutrients based on absorption rates (heme vs non-heme iron, etc.)
- **Anti-Nutrient Management** - Preparation instructions to reduce phytates, oxalates, lectins
- **Synergy Analyzer** - Identifies nutrient combinations that enhance or inhibit absorption
- **Smart Warnings** - Real-time alerts for nutrient interactions and optimal timing

### Multi-User System (NEW!)
- **Firebase Authentication** - Email/password and Google sign-in
- **Cloud Data Sync** - Meal plans and biomarkers stored per user in Firestore
- **Cross-Device Access** - Login from any device, data syncs automatically
- **Secure Data Isolation** - Users can't access others' data

## Core Principles
- **Whole Foods Only**: No processed oils, synthetic ingredients, or heavily refined foods
- **Non-GMO**: Exclusively traditional, non-genetically modified ingredients
- **Ancestral Grains**: Avoiding modern hybridized wheat; using ancient grains (einkorn, spelt, etc.)
- **Nutrient Density**: Prioritizing foods with highest bioavailable nutrients
- **Optimal Health**: Based on scientific research for thriving, not just avoiding deficiency

## Research Foundation
Nutritional requirements based on:
- WHO/FAO international guidelines
- Peer-reviewed scientific literature and meta-analyses
- Functional medicine optimization protocols (Function Health biomarker ranges)
- Traditional diets and anthropological nutrition research
## 🚀 Quick Start

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Firebase account (free) - Get at https://console.firebase.google.com
- GitHub account (for deployment)

### Local Development
```powershell
cd c:\Users\Sdela\vcodeprojects\HealthApp\web
python -m http.server 8000
```
Open: http://localhost:8000/auth.html

### Deployment
See detailed setup instructions in [FIREBASE_SETUP.md](FIREBASE_SETUP.md)

**Quick version:**
1. Create Firebase project (5 min)
2. Enable Authentication + Firestore (3 min)
3. Update `web/firebase-config.js` with your credentials
4. Deploy to GitHub Pages (10 min)
5. Add GitHub domain to Firebase authorized domains

## 📁 Project Structure

```
HealthApp/
├── web/                          # Frontend application
│   ├── auth.html                 # Login/signup page (NEW!)
│   ├── index.html                # Main application
│   ├── styles.css                # Complete styling
│   ├── app.js                    # Application logic + Firestore integration
│   ├── auth.js                   # Authentication logic (NEW!)
│   └── firebase-config.js        # Firebase configuration - UPDATE THIS!
├── data/
│   ├── recipes/
│   │   └── recipe-database.json  # 30+ whole-food recipes
│   ├── nutrition-requirements/
│   │   └── nutrient-interactions.json  # Bioavailability & synergy data
│   └── biomarkers/
│       └── function-health-integration.json  # Lab ranges & recommendations
├── FIREBASE_SETUP.md             # Detailed setup guide (NEW!)
├── QUICK_START.md                # Quick reference (NEW!)
├── .gitignore                    # Git ignore file (NEW!)
└── README.md                     # This file
```

## 🔧 Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Authentication**: Firebase Auth (Email/Password + Google)
- **Database**: Cloud Firestore (NoSQL)
- **Hosting**: GitHub Pages (free HTTPS)
- **No build step required** - Pure static files

## 💰 Cost

**FREE** for personal use:
- Firebase Spark Plan: 50K auth users/month, 50K Firestore reads/day, 20K writes/day
- GitHub Pages: Unlimited bandwidth, free HTTPS

**Paid upgrade needed only if:**
- 10+ heavy daily users (~$5-10/month)
- Need phone authentication or advanced features

## 🔒 Security

- ✅ User authentication required for all features
- ✅ Firestore security rules enforce data isolation
- ✅ HTTPS enforced on GitHub Pages
- ✅ No API keys in public code (Firebase config is public by design)
- ✅ Password requirements: minimum 6 characters

## 📊 Data Model

### Firestore Structure
```
users/{userId}/
├── email, displayName, photoURL, createdAt
├── preferences: { servings: 4, theme: 'light' }
├── mealPlans/current/
│   ├── plan: { monday: {...}, tuesday: {...}, ... }
│   └── updatedAt
└── biomarkers/latest/
    ├── markers: { vitaminD: 42, ferritin: 68, ... }
    └── updatedAt
```

## 🎯 Use Cases

1. **Personal Nutrition Optimization**
   - Track meals and nutrients across devices
   - Monitor biomarker trends over time
   - Get personalized meal recommendations from lab results

2. **Family Meal Planning**
   - Plan weekly meals for 1-6 people
   - Scale recipes automatically
   - Ensure complete nutrition for all family members

3. **Health Coaching**
   - Clients create their own accounts
   - Track progress independently
   - Generate meal recommendations from Function Health results

## 🧪 Testing Checklist

- [ ] Signup with email/password
- [ ] Login with Google account
- [ ] Add recipes to weekly meal plan
- [ ] Save meal plan (should sync to Firestore)
- [ ] Enter biomarker values
- [ ] Get personalized recommendations
- [ ] Save biomarkers (should sync to Firestore)
- [ ] Logout and login from different device
- [ ] Verify data persists across devices
- [ ] Test user menu dropdown

## 📝 Future Enhancements

- [ ] Import/export JSON meal plans and biomarkers
- [ ] Advanced recipe search with filters
- [ ] Automatic shopping list generation
- [ ] Mobile app (React Native or PWA)
- [ ] Biomarker trend charts over time
- [ ] Social features (share recipes with friends)
- [ ] Meal prep batch cooking instructions
- [ ] Integration with wearables (Apple Health, Google Fit)

## 🤝 Contributing

This is a personal project, but suggestions welcome! Open an issue or submit a pull request.

## 📄 License

MIT License - Free to use and modify

## 🙏 Acknowledgments

- Nutrition data based on USDA FoodData Central
- Bioavailability research from peer-reviewed studies
- Function Health for biomarker optimization ranges
- Firebase for backend infrastructure and auth

## 📧 Support

For issues or questions:
1. Check [FIREBASE_SETUP.md](FIREBASE_SETUP.md) troubleshooting section
2. Review browser console (F12) for errors
3. Verify Firebase configuration in `firebase-config.js` is correct
4. Ensure authorized domains are set in Firebase Console

---

**Built with ❤️ for optimal nutrition and health**