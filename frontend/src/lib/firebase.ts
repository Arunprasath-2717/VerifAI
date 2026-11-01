import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as fbSignOut,
  updateProfile,
  sendPasswordResetEmail,
  onAuthStateChanged,
  User as FirebaseUser,
  getIdToken,
  Auth,
  GoogleAuthProvider,
  signInWithPopup,
} from "firebase/auth";
import { getAnalytics, isSupported, Analytics } from "firebase/analytics";
import { authApi, TokenResponse } from "../api/auth";

// VerifAI Web Firebase Configuration
export const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDag7_lFm6ayphrJUDYWK2EQmZmFdaU_5s",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "verifai-22c4b.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "verifai-22c4b",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "verifai-22c4b.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "501647364420",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:501647364420:web:9848f5dc7ba7d236704711",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-4LPP8CZGG3",
};

// Singleton Firebase Application instance
export const app: FirebaseApp = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// Firebase Authentication instance
export const auth: Auth = getAuth(app);

// Safe browser Analytics instance
export let analytics: Analytics | null = null;
if (typeof window !== "undefined") {
  isSupported()
    .then((supported) => {
      if (supported) {
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
  firebaseUser: FirebaseUser;
  tokenResponse: TokenResponse | null;
  email: string;
  displayName: string;
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
  try {
    await fbSignOut(auth);
  } catch (err) {
    console.warn("Firebase sign out error:", err);
  } finally {
    authApi.logout();
  }
}

/**
 * Trigger password reset email via Firebase.
 */
export async function firebaseResetPassword(email: string): Promise<void> {
  const cleanEmail = email.trim().toLowerCase();
  await sendPasswordResetEmail(auth, cleanEmail);
}

/**
 * Retrieve current Firebase user.
 */
export function getCurrentFirebaseUser(): FirebaseUser | null {
  return auth.currentUser;
}

/**
 * Retrieve active Firebase ID token (refreshes if expired).
 */
export async function getFirebaseIdToken(forceRefresh = false): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken(forceRefresh);
}

export { onAuthStateChanged };
export type { FirebaseUser };
