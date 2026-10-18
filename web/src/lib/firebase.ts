import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getAnalytics, isSupported } from 'firebase/analytics';

export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyDCVHrBCdpFCpIm_R3o-Zlse4gzvNafre8',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'quantdb-728ef.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'quantdb-728ef',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'quantdb-728ef.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '902285866945',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:902285866945:web:197ad914d3bf1d8070a140',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || 'G-7WCQ2VMPQ8',
};

// Initialize Firebase App singleton
export const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Firebase Services
export const auth = getAuth(app);
export const db = getFirestore(app);

// Analytics (safely initialized in supported browser contexts)
export const analyticsPromise = typeof window !== 'undefined'
  ? isSupported().then((supported) => (supported ? getAnalytics(app) : null)).catch(() => null)
  : Promise.resolve(null);

export default app;
