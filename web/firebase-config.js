// Firebase Configuration
// Connected to: healthapp-9c646

const firebaseConfig = {
    apiKey: "AIzaSyACdoYrPt4MPwQ-zU7_aAqmNjayTC7iVt8",
    authDomain: "healthapp-9c646.firebaseapp.com",
    projectId: "healthapp-9c646",
    storageBucket: "healthapp-9c646.firebasestorage.app",
    messagingSenderId: "1008682728530",
    appId: "1:1008682728530:web:4851025119ba0ed473738b",
    measurementId: "G-M9DL7FVR4B"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize services
const auth = firebase.auth();
const db = firebase.firestore();

console.log('Firebase initialized successfully');
