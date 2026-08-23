import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  User,
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signOut as firebaseSignOut
} from 'firebase/auth';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { auth, googleProvider, db } from '../lib/firebase';
import { platformAdminErisiminiGetir } from '../lib/api';

export type UserRole = 'admin' | 'cfo' | 'analyst' | 'viewer' | 'member';

export interface UserProfile {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  role: UserRole;
  companyName: string;
  companyId: string | null;
  createdAt: string;
  plan?: 'free' | 'trial' | 'pro' | 'uzman';
  trialEndsAt?: string;
  onboardingProfile?: {
    sector: string;
    employeeScale: string;
    primaryGoal: string;
    primaryChallenge: string;
    dataSource: string;
    availableData: string[];
    currency: string;
    fiscalYearStartMonth: number;
    source: 'self_reported_onboarding';
  };
}

interface AuthContextType {
  currentUser: User | null;
  userProfile: UserProfile | null;
  loading: boolean;
  isGuest: boolean;
  isPlatformAdmin: boolean;
  loginWithGoogle: () => Promise<void>;
  loginWithEmail: (e: string, p: string) => Promise<void>;
  signUpWithEmail: (e: string, p: string, name: string) => Promise<void>;
  resetPassword: (e: string) => Promise<void>;
  logout: () => Promise<void>;
  enableGuestMode: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

async function loadUserProfile(user: User): Promise<UserProfile> {
  const userDocRef = doc(db, 'users', user.uid);
  const snap = await getDoc(userDocRef);
  if (snap.exists()) return snap.data() as UserProfile;

  const newProfile: UserProfile = {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName || user.email?.split('@')[0] || 'Kullanıcı',
    photoURL: user.photoURL,
    role: 'member',
    companyName: 'Şirket üyeliği bekleniyor',
    companyId: null,
    createdAt: new Date().toISOString(),
    plan: 'free',
  };
  await setDoc(userDocRef, newProfile);
  return newProfile;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isGuest, setIsGuest] = useState<boolean>(false);
  const [isPlatformAdmin, setIsPlatformAdmin] = useState<boolean>(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        setCurrentUser(user);
        setIsGuest(false);
        try {
          setUserProfile(await loadUserProfile(user));
        } catch (err) {
          console.warn('Firestore user profile fetch warning:', err);
          setUserProfile({
            uid: user.uid,
            email: user.email,
            displayName: user.displayName || 'Kullanıcı',
            photoURL: user.photoURL,
            role: 'member',
            companyName: 'Profil doğrulanamadı',
            companyId: null,
            createdAt: new Date().toISOString(),
            plan: 'free',
          });
        }
      } else {
        setCurrentUser(null);
        setUserProfile(null);
      }
      try { setIsPlatformAdmin(await platformAdminErisiminiGetir()); }
      catch { setIsPlatformAdmin(false); }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const loginWithGoogle = async () => {
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err: any) {
      console.error('Google Sign-In error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const loginWithEmail = async (email: string, pass: string) => {
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email.trim().toLowerCase(), pass);
    } finally {
      setLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, pass: string, name: string) => {
    setLoading(true);
    try {
      const res = await createUserWithEmailAndPassword(auth, email.trim().toLowerCase(), pass);
      const newProfile: UserProfile = {
        uid: res.user.uid,
        email: res.user.email,
        displayName: name,
        photoURL: null,
        role: 'member',
        companyName: 'Şirket üyeliği bekleniyor',
        companyId: null,
        createdAt: new Date().toISOString(),
        plan: 'free',
      };
      await setDoc(doc(db, 'users', res.user.uid), newProfile);
      setUserProfile(newProfile);
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      const error = new Error('E-posta adresi gerekli.') as Error & { code: string };
      error.code = 'auth/missing-email';
      throw error;
    }
    await sendPasswordResetEmail(auth, normalizedEmail);
  };

  const logout = async () => {
    await firebaseSignOut(auth);
    setIsGuest(false);
    setCurrentUser(null);
    setUserProfile(null);
    setIsPlatformAdmin(false);
  };

  const refreshProfile = async () => {
    const user = auth.currentUser;
    if (!user) return;
    setUserProfile(await loadUserProfile(user));
  };

  const enableGuestMode = () => {
    setIsGuest(true);
    setUserProfile({
      uid: 'guest-user-123',
      email: 'demo@kazkaz.ai',
      displayName: 'Misafir Finans Yetkilisi',
      photoURL: null,
      role: 'analyst',
      companyName: 'Anadolu Teknoloji A.Ş. (Demo)',
      companyId: null,
      createdAt: new Date().toISOString(),
      plan: 'uzman',
    });
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        userProfile,
        loading,
        isGuest,
        isPlatformAdmin,
        loginWithGoogle,
        loginWithEmail,
        signUpWithEmail,
        resetPassword,
        logout,
        enableGuestMode,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
