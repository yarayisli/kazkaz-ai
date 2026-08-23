import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
};

if (!firebaseConfig.projectId || !firebaseConfig.appId || !firebaseConfig.apiKey) {
  throw new Error('Firebase web yapılandırması eksik. web/.env.example dosyasını temel alın.');
}

const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// Initialize Auth
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Firestore (supporting custom database ID if specified)
export const db = import.meta.env.VITE_FIREBASE_DATABASE_ID
  ? getFirestore(app, import.meta.env.VITE_FIREBASE_DATABASE_ID)
  : getFirestore(app);

export default app;
