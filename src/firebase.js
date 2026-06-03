import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

// Firebase configuration — uses Vite env vars so it works on Vercel
// without needing the gitignored firebase-config.json file.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAoZusx_BIBHDK-__SlP7cHiLhTxn40yrk",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "mindnest-de930.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "mindnest-de930",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "mindnest-de930.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "542998778808",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:542998778808:web:9679ba69581102759bb54d",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-95P5NLJK8Q",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Cloud Firestore and get a reference to the service
export const db = getFirestore(app);

// Initialize Firebase Authentication
export const auth = getAuth(app);
