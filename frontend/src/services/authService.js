/**
 * VerifAI Authentication Service
 * Manages Firebase User Sessions and Token Propagation to the Backend API.
 */
import {
  auth,
  googleProvider,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from "../firebase.js";

const BACKEND_API_BASE = "http://localhost:8000/api/v1";

export class AuthService {
  /**
   * Log in with Email and Password.
   */
  static async login(email, password) {
    const cred = await signInWithEmailAndPassword(auth, email, password);
    const token = await cred.user.getIdToken();
    await this.syncWithBackend(token);
    return cred.user;
  }

  /**
   * Register with Email and Password.
   */
  static async register(email, password) {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    const token = await cred.user.getIdToken();
    await this.syncWithBackend(token);
    return cred.user;
  }

  /**
   * Sign in using Google OAuth Popup.
   */
  static async loginWithGoogle() {
    const cred = await signInWithPopup(auth, googleProvider);
    const token = await cred.user.getIdToken();
    await this.syncWithBackend(token);
    return cred.user;
  }

  /**
   * Sign out current user from Firebase and clear tokens.
   */
  static async logout() {
    await signOut(auth);
    localStorage.removeItem("verifai_token");
    localStorage.removeItem("verifai_user");
  }

  /**
   * Get the current user's active Firebase ID token (auto-refreshed by Firebase).
   */
  static async getIdToken(forceRefresh = false) {
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken(forceRefresh);
  }

  /**
   * Synchronize the Firebase ID token with VerifAI backend.
   */
  static async syncWithBackend(idToken) {
    try {
      const resp = await fetch(`${BACKEND_API_BASE}/auth/firebase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });
      if (resp.ok) {
        const data = await resp.json();
        localStorage.setItem("verifai_token", data.access_token);
        localStorage.setItem("verifai_user", JSON.stringify(data));
        return data;
      }
    } catch (err) {
      console.warn("Could not sync Firebase token with backend:", err);
    }
    return null;
  }

  /**
   * Listen to Firebase Auth state changes.
   */
  static onAuthStateChanged(callback) {
    return onAuthStateChanged(auth, async (user) => {
      if (user) {
        const token = await user.getIdToken();
        localStorage.setItem("verifai_firebase_token", token);
      } else {
        localStorage.removeItem("verifai_firebase_token");
        localStorage.removeItem("verifai_token");
      }
      callback(user);
    });
  }

  /**
   * Get authorized fetch headers with Bearer token for API calls.
   */
  static async getAuthHeaders() {
    const token = (await this.getIdToken()) || localStorage.getItem("verifai_token");
    const headers = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }
}

export default AuthService;
