/**
 * VerifAI — Firebase Application & Authentication Initialization
 */
import { initializeApp } from "firebase/app";
import { getAnalytics, isSupported } from "firebase/analytics";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";

// Your web app's Firebase configuration
export const firebaseConfig = {
  apiKey: "AIzaSyDag7_lFm6ayphrJUDYWK2EQmZmFdaU_5s",
  authDomain: "verifai-22c4b.firebaseapp.com",
  projectId: "verifai-22c4b",
  storageBucket: "verifai-22c4b.firebasestorage.app",
  messagingSenderId: "501647364420",
  appId: "1:501647364420:web:9848f5dc7ba7d236704711",
  measurementId: "G-4LPP8CZGG3",
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Analytics conditionally (only in supported browser environments)
export let analytics = null;
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  });
}

export {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
};
