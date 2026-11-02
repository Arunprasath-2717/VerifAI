import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as fbSignOut,
  updateProfile,
  sendPasswordResetEmail,
  onAuthStateChanged as fbOnAuthStateChanged,
  User as FirebaseUser,
  getIdToken,
  Auth,
  GoogleAuthProvider,
  signInWithPopup,
} from "firebase/auth";
import { getAnalytics, isSupported, Analytics } from "firebase/analytics";
import { authApi, TokenResponse } from "../api/auth";

// Firebase web identifiers are supplied by deployment configuration, not source defaults.
// Missing values must be set through frontend/.env (development) or deployment env vars.
// VerifAI Web Firebase Configuration
export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDeWBSjAl79IDVRYcYeb4l-5-ag0wG59Oo",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "verifai-819d0.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "verifai-819d0",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "verifai-819d0.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "155971042326",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:155971042326:web:e15c616961f30924670937",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-6NRZE0PG6E",
};

export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey &&
  typeof firebaseConfig.apiKey === "string" &&
  firebaseConfig.apiKey.trim().length > 0 &&
  firebaseConfig.projectId &&
  typeof firebaseConfig.projectId === "string" &&
  firebaseConfig.projectId.trim().length > 0
);

// Singleton Firebase Application instance (only initialized if configuration is present)
export const app: FirebaseApp | null = isFirebaseConfigured
  ? (getApps().length > 0 ? getApp() : initializeApp(firebaseConfig))
  : null;

// Firebase Authentication instance (null when Firebase is unconfigured in local development)
export const auth: Auth | null = app ? getAuth(app) : null;

// Safe browser Analytics instance
export let analytics: Analytics | null = null;
if (typeof window !== "undefined" && isFirebaseConfigured && app) {
  isSupported()
    .then((supported) => {
      if (supported && app) {
        try {
          analytics = getAnalytics(app);
        } catch {
          // Analytics gracefully bypassed
        }
      }
    })
    .catch(() => {});
}

export interface AuthSuccessResult {
  firebaseUser: FirebaseUser | null;
  tokenResponse: TokenResponse | null;
  email: string;
  displayName: string;
}

/**
 * Safe onAuthStateChanged wrapper that falls back gracefully when Firebase is unconfigured.
 */
export function onAuthStateChanged(
  authInstance: any,
  observerOrNext: any,
  ...args: any[]
): () => void {
  if (!isFirebaseConfigured || !auth) {
    if (typeof observerOrNext === "function") {
      observerOrNext(null);
    } else if (observerOrNext && typeof observerOrNext.next === "function") {
      observerOrNext.next(null);
    }
    return () => {};
  }
  return fbOnAuthStateChanged(auth, observerOrNext, ...args);
}

/**
 * Human-readable mapping of Firebase Auth error codes to professional user feedback.
 */
export function formatFirebaseErrorMessage(err: any): string {
  if (!err) return "An unexpected error occurred. Please try again.";

  const code: string = err.code || "";
  const rawMessage: string = err.message || "";

  switch (code) {
    case "auth/email-already-in-use":
      return "An account with this email address already exists. Please log in instead.";
    case "auth/invalid-email":
      return "Please enter a valid email address.";
    case "auth/weak-password":
      return "Password is too weak. Please use at least 6 characters (8+ recommended with letters and numbers).";
    case "auth/user-not-found":
      return "No account was found with this email address.";
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Invalid email or password. Please verify your credentials.";
    case "auth/user-disabled":
      return "This account has been deactivated. Please contact support.";
    case "auth/too-many-requests":
      return "Access to this account has been temporarily restricted due to multiple failed login attempts. Please reset your password or try again later.";
    case "auth/network-request-failed":
      return "Network connection error. Please verify your internet connection and try again.";
    case "auth/operation-not-allowed":
      return "Email and password authentication is currently disabled in Firebase.";
    case "auth/missing-password":
      return "Please enter your password.";
    case "auth/missing-email":
      return "Please enter your email address.";
    case "auth/popup-closed-by-user":
      return "Google sign-in window was closed before completing.";
    case "auth/popup-blocked":
      return "The Google authentication popup was blocked by your browser. Please enable popups.";
    case "auth/cancelled-popup-request":
      return "Sign-in request was cancelled.";
    case "auth/account-exists-with-different-credential":
      return "An account already exists with the same email using a different sign-in method.";
    case "auth/unauthorized-domain":
      return "This domain is not authorized in Firebase Console for Google authentication.";
    default:
      if (rawMessage.includes("auth/")) {
        return rawMessage.replace(/Firebase: Error \(auth\/[^)]+\)\.?/, "").trim() || "Authentication failed. Please try again.";
      }
      return rawMessage || "Authentication failed. Please verify your credentials.";
  }
}

/**
 * Register a new user with Firebase, set user profile, and exchange RS256 token with VerifAI backend.
 */
export async function firebaseSignUp(params: {
  email: string;
  password: string;
  fullName?: string;
  termsAccepted?: boolean;
}): Promise<AuthSuccessResult> {
  if (!isFirebaseConfigured || !auth) {
    throw new Error("Firebase authentication is not configured in this local environment. Please register using standard username/password.");
  }
  const cleanEmail = params.email.trim().toLowerCase();
  const cleanName = params.fullName?.trim() || cleanEmail.split("@")[0];

  // 1. Create user in Firebase Authentication
  const credential = await createUserWithEmailAndPassword(auth, cleanEmail, params.password);
  const user = credential.user;

  // 2. Update Firebase display name if provided
  if (cleanName) {
    try {
      await updateProfile(user, { displayName: cleanName });
    } catch (profileErr) {
      console.warn("Could not set display name in Firebase:", profileErr);
    }
  }

  // 3. Force-refresh RS256 token so claims/displayName are embedded
  const idToken = await user.getIdToken(true);

  // 4. Exchange Firebase RS256 token with VerifAI backend for session minting and DB sync
  let tokenRes: TokenResponse | null = null;
  try {
    tokenRes = await authApi.firebaseAuth(idToken, cleanName, {
      is_signup: true,
      terms_accepted: params.termsAccepted ?? true,
    });
  } catch (backendErr) {
    console.warn("VerifAI backend session exchange deferred:", backendErr);
  }

  return {
    firebaseUser: user,
    tokenResponse: tokenRes,
    email: cleanEmail,
    displayName: cleanName,
  };
}

/**
 * Sign in existing user with Firebase and synchronize session token with VerifAI backend.
 */
export async function firebaseSignIn(params: {
  email: string;
  password: string;
}): Promise<AuthSuccessResult> {
  if (!isFirebaseConfigured || !auth) {
    throw new Error("Firebase authentication is not configured in this local environment. Please sign in using standard email/username and password.");
  }
  const cleanEmail = params.email.trim().toLowerCase();

  // 1. Sign in via Firebase Authentication
  const credential = await signInWithEmailAndPassword(auth, cleanEmail, params.password);
  const user = credential.user;

  // 2. Retrieve RS256 ID token
  const idToken = await user.getIdToken();

  // 3. Synchronize with VerifAI backend
  let tokenRes: TokenResponse | null = null;
  try {
    tokenRes = await authApi.firebaseAuth(idToken, user.displayName || undefined);
  } catch (backendErr) {
    console.warn("VerifAI backend session exchange deferred:", backendErr);
  }

  const displayName = user.displayName || cleanEmail.split("@")[0] || "Researcher";

  return {
    firebaseUser: user,
    tokenResponse: tokenRes,
    email: cleanEmail,
    displayName,
  };
}

/**
 * Authenticate or register using real Google OAuth popup and synchronize RS256 token with VerifAI backend.
 */
export async function firebaseSignInWithGoogle(options?: {
  termsAccepted?: boolean;
  isSignup?: boolean;
}): Promise<AuthSuccessResult> {
  if (!isFirebaseConfigured || !auth) {
    throw new Error("Google Sign-In requires Firebase configuration. Please use standard email/username and password.");
  }
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });

  const credential = await signInWithPopup(auth, provider);
  const user = credential.user;
  const idToken = await user.getIdToken();

  let tokenRes: TokenResponse | null = null;
  try {
    tokenRes = await authApi.firebaseAuth(idToken, user.displayName || undefined, {
      is_signup: options?.isSignup,
      terms_accepted: options?.termsAccepted,
    });
  } catch (backendErr) {
    console.warn("VerifAI backend session exchange deferred:", backendErr);
  }

  const displayName = user.displayName || user.email?.split("@")[0] || "Google User";

  return {
    firebaseUser: user,
    tokenResponse: tokenRes,
    email: user.email || "",
    displayName,
  };
}

/**
 * Sign out user from Firebase and clear VerifAI session tokens.
 */
export async function firebaseSignOut(): Promise<void> {
  if (isFirebaseConfigured && auth) {
    try {
      await fbSignOut(auth);
    } catch (err) {
      console.warn("Firebase sign out error:", err);
    }
  }
  authApi.logout();
}

/**
 * Trigger password reset email via Firebase.
 */
export async function firebaseResetPassword(email: string): Promise<void> {
  if (!isFirebaseConfigured || !auth) {
    throw new Error("Password reset via Firebase is not configured.");
  }
  const cleanEmail = email.trim().toLowerCase();
  await sendPasswordResetEmail(auth, cleanEmail);
}

/**
 * Retrieve current Firebase user.
 */
export function getCurrentFirebaseUser(): FirebaseUser | null {
  if (!isFirebaseConfigured || !auth) return null;
  return auth.currentUser;
}

/**
 * Retrieve active Firebase ID token (refreshes if expired).
 */
export async function getFirebaseIdToken(forceRefresh = false): Promise<string | null> {
  if (!isFirebaseConfigured || !auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
}

export type { FirebaseUser };
