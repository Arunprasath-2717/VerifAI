import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  auth,
  onAuthStateChanged,
  FirebaseUser,
  firebaseSignUp,
  firebaseSignIn,
  firebaseSignInWithGoogle,
  firebaseSignOut,
  firebaseResetPassword,
  formatFirebaseErrorMessage,
} from '../lib/firebase';
import { authApi, UserResponse, TokenResponse } from '../api/auth';
import { getAuthToken, setAuthToken } from '../api/client';

export interface AuthContextType {
  user: UserResponse | null;
  firebaseUser: FirebaseUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<TokenResponse | null>;
  signInWithGoogle: () => Promise<TokenResponse | null>;
  signUp: (email: string, password: string, fullName?: string) => Promise<TokenResponse | null>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  refreshProfile: () => Promise<UserResponse | null>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      return localStorage.getItem('verifai_authenticated') === 'true' && Boolean(localStorage.getItem('verifai_token'));
    } catch {
      return false;
    }
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshProfile = useCallback(async (): Promise<UserResponse | null> => {
    try {
      const profile = await authApi.getMe();
      setUser(profile);
      setIsAuthenticated(true);
      return profile;
    } catch (err) {
      console.warn('Failed to load user profile from backend:', err);
      return null;
    }
  }, []);

  // Listen to Firebase Authentication state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setFirebaseUser(fbUser);

      if (fbUser) {
        try {
          // Obtain current RS256 token and sync with backend
          const idToken = await fbUser.getIdToken();
          const tokenRes = await authApi.firebaseAuth(idToken, fbUser.displayName || undefined);
          if (tokenRes.access_token) {
            setAuthToken(tokenRes.access_token);
          }
          await refreshProfile();
          setIsAuthenticated(true);
        } catch (syncErr) {
          console.warn('Backend sync during onAuthStateChanged:', syncErr);
          // Retain authenticated status if Firebase user is valid
          setIsAuthenticated(true);
        }
      } else {
        // Firebase has no active user
        const existingToken = getAuthToken();
        if (existingToken) {
          // Check if VerifAI local session is still valid
          try {
            await refreshProfile();
            setIsAuthenticated(true);
          } catch {
            setAuthToken(null);
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
      }

      setIsLoading(false);
    });

    return () => unsubscribe();
  }, [refreshProfile]);

  const signIn = async (email: string, password: string): Promise<TokenResponse | null> => {
    setError(null);
    try {
      const res = await firebaseSignIn({ email, password });
      setFirebaseUser(res.firebaseUser);
      setIsAuthenticated(true);
      if (res.tokenResponse?.access_token) {
        setAuthToken(res.tokenResponse.access_token);
        await refreshProfile();
      }
      return res.tokenResponse;
    } catch (err: any) {
      const friendlyMsg = formatFirebaseErrorMessage(err);
      setError(friendlyMsg);
      throw new Error(friendlyMsg);
    }
  };

  const signUp = async (
    email: string,
    password: string,
    fullName?: string
  ): Promise<TokenResponse | null> => {
    setError(null);
    try {
      const res = await firebaseSignUp({ email, password, fullName });
      setFirebaseUser(res.firebaseUser);
      setIsAuthenticated(true);
      if (res.tokenResponse?.access_token) {
        setAuthToken(res.tokenResponse.access_token);
        await refreshProfile();
      }
      return res.tokenResponse;
    } catch (err: any) {
      const friendlyMsg = formatFirebaseErrorMessage(err);
      setError(friendlyMsg);
      throw new Error(friendlyMsg);
    }
  };

  const signInWithGoogle = async (): Promise<TokenResponse | null> => {
    setError(null);
    try {
      const res = await firebaseSignInWithGoogle();
      setFirebaseUser(res.firebaseUser);
      setIsAuthenticated(true);
      if (res.tokenResponse?.access_token) {
        setAuthToken(res.tokenResponse.access_token);
        await refreshProfile();
      }
      return res.tokenResponse;
    } catch (err: any) {
      const friendlyMsg = formatFirebaseErrorMessage(err);
      setError(friendlyMsg);
      throw new Error(friendlyMsg);
    }
  };

  const signOut = async (): Promise<void> => {
    setError(null);
    try {
      await firebaseSignOut();
    } finally {
      setFirebaseUser(null);
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const resetPassword = async (email: string): Promise<void> => {
    setError(null);
    try {
      await firebaseResetPassword(email);
    } catch (err: any) {
      const friendlyMsg = formatFirebaseErrorMessage(err);
      setError(friendlyMsg);
      throw new Error(friendlyMsg);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        firebaseUser,
        isAuthenticated,
        isLoading,
        error,
        signIn,
        signInWithGoogle,
        signUp,
        signOut,
        resetPassword,
        refreshProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
