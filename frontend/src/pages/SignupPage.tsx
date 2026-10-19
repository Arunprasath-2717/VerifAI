import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  AlertCircle, 
  ArrowLeft, 
  Lock, 
  Mail, 
  User, 
  ShieldCheck,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import authFluidRibbon from '../assets/auth_fluid_ribbon.jpg';
import authBackdropRibbon from '../assets/auth_backdrop_ribbon.jpg';
import { 
  firebaseSignUp, 
  firebaseSignIn, 
  firebaseSignInWithGoogle, 
  firebaseSignOut, 
  firebaseResetPassword, 
  formatFirebaseErrorMessage 
} from '../lib/firebase';
import { setAuthToken } from '../api/client';
import { PolicyModal, PolicyTab } from '../components/legal/PolicyModal';

interface SignupPageProps {
  initialMode?: 'signup' | 'login';
  theme?: 'light' | 'dark';
  onAuthSuccess?: (user: { fullName: string; email: string }) => void;
  isAuthenticated?: boolean;
}

export const SignupPage: React.FC<SignupPageProps> = ({
  initialMode = 'login',
  onAuthSuccess,
  isAuthenticated = false,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Mode: 'login' | 'signup' | 'forgot-password'
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot-password'>(() => {
    if (location.pathname === '/signup') return 'signup';
    if (location.pathname === '/login') return 'login';
    return initialMode;
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Synchronize mode with route changes
  useEffect(() => {
    if (location.pathname === '/signup') {
      setMode('signup');
    } else if (location.pathname === '/login') {
      setMode('login');
    } else if (location.pathname === '/' && mode !== 'forgot-password') {
      setMode(initialMode);
    }
  }, [location.pathname, initialMode]);

  // Form Fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [agreeTerms, setAgreeTerms] = useState(false);

  // Policy Modal & Validation Error States
  const [policyModalOpen, setPolicyModalOpen] = useState(false);
  const [policyModalTab, setPolicyModalTab] = useState<PolicyTab>('terms');
  const [consentError, setConsentError] = useState<string | null>(null);

  // Status & Feedback States
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Forgot password specific email
  const [resetEmail, setResetEmail] = useState('');
  const [isResetSending, setIsResetSending] = useState(false);

  // Password requirement validation helpers
  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const hasLetter = /[a-zA-Z]/.test(password);

  const cleanEmail = email.trim().toLowerCase();
  const cleanName = name.trim();

  const switchMode = (newMode: 'signup' | 'login' | 'forgot-password') => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setConsentError(null);
    setMode(newMode);
    if (newMode === 'signup') {
      navigate('/signup');
    } else if (newMode === 'login') {
      navigate('/login');
    }
  };

  const handlePasswordResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const targetEmail = (resetEmail || email).trim();
    if (!targetEmail || !targetEmail.includes('@')) {
      setErrorMessage('Please provide a valid email address for password recovery.');
      return;
    }

    setIsResetSending(true);

    try {
      await firebaseResetPassword(targetEmail);
      setIsResetSending(false);
      setSuccessMessage(
        `A password recovery link has been dispatched to ${targetEmail}. Please check your inbox.`
      );
    } catch (err: any) {
      setIsResetSending(false);
      setErrorMessage(formatFirebaseErrorMessage(err));
    }
  };

  const handleGoogleAuth = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setConsentError(null);

    if (mode === 'signup' && !agreeTerms) {
      setConsentError('You must read and agree to the Terms & Conditions before signing up.');
      setErrorMessage('Please accept the Terms & Conditions and Privacy Policy before proceeding.');
      return;
    }

    setIsGoogleLoading(true);

    try {
      const result = await firebaseSignInWithGoogle({
        isSignup: mode === 'signup',
        termsAccepted: mode === 'signup' ? agreeTerms : true,
      });

      if (result.tokenResponse?.access_token) {
        setAuthToken(result.tokenResponse.access_token);
      }
      setIsGoogleLoading(false);
      setSuccessMessage(`Welcome, ${result.displayName}! Loading console...`);

      if (onAuthSuccess) {
        onAuthSuccess({
          fullName: result.displayName,
          email: result.email,
        });
      }

      setTimeout(() => {
        navigate('/dashboard');
      }, 400);
    } catch (err: any) {
      setIsGoogleLoading(false);
      setErrorMessage(formatFirebaseErrorMessage(err));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setConsentError(null);

    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setErrorMessage('Please enter a valid work or academic email address.');
      return;
    }

    if (mode === 'signup') {
      if (!cleanName) {
        setErrorMessage('Please provide your full name.');
        return;
      }
      if (!hasMinLength) {
        setErrorMessage('Password must be at least 8 characters in length.');
        return;
      }
      if (!hasLetter || !hasNumber) {
        setErrorMessage('Password must contain both letters and digits.');
        return;
      }
      if (password !== confirmPassword) {
        setErrorMessage('Passwords do not match. Please verify your confirmation password.');
        return;
      }
      if (!agreeTerms) {
        setConsentError('You must agree to the Terms & Conditions and Privacy Policy.');
        setErrorMessage('Please accept the Terms & Conditions and Privacy Policy to continue.');
        return;
      }
    } else {
      if (!password) {
        setErrorMessage('Please enter your password.');
        return;
      }
    }

    setIsLoading(true);

    try {
      if (mode === 'signup') {
        await firebaseSignUp({
          email: cleanEmail,
          password,
          fullName: cleanName,
          termsAccepted: true,
        });

        await firebaseSignOut();
        setIsLoading(false);
        setPassword('');
        setConfirmPassword('');
        setAgreeTerms(false);
        setMode('login');
        navigate('/login');
        setSuccessMessage('Account created successfully! Please sign in with your credentials.');
      } else {
        const result = await firebaseSignIn({
          email: cleanEmail,
          password,
        });

        if (result.tokenResponse?.access_token) {
          setAuthToken(result.tokenResponse.access_token);
        }

        setIsLoading(false);
        setSuccessMessage('Authentication successful! Loading intelligence workspace...');

        if (onAuthSuccess) {
          onAuthSuccess({
            fullName: result.displayName || cleanEmail.split('@')[0],
            email: cleanEmail,
          });
        }

        setTimeout(() => {
          navigate('/dashboard');
        }, 400);
      }
    } catch (err: any) {
      setIsLoading(false);
      setErrorMessage(formatFirebaseErrorMessage(err));
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-[#07070a] text-white overflow-x-hidden p-4 sm:p-6 md:p-8 select-none">
      
      {/* ─────────────────────────────────────────────────────────────
          OUTER AMBIENT BACKDROP:
          Vibrant dark canvas with flowing 3D ribbon aura matching screenshot
          ───────────────────────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <img
          src={authBackdropRibbon}
          alt=""
          className="w-full h-full object-cover object-center opacity-45 scale-105 filter blur-[2px]"
        />
        {/* Deep ambient dark vignettes around the edges */}
        <div className="absolute inset-0 bg-radial-[ellipse_at_center,_transparent_30%,_#050508_85%]" />
        <div className="absolute inset-0 bg-[#07070a]/60 backdrop-blur-[1px]" />
      </div>

      {/* ─────────────────────────────────────────────────────────────
          MAIN FLOATING CARD CONTAINER:
          Matching the reference layout with rounded-4xl, crisp white boundary,
          two-column split (Hero left, Crisp white form right)
          ───────────────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-[1080px] bg-black rounded-[36px] sm:rounded-[42px] border border-white/80 shadow-[0_30px_100px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col lg:flex-row"
      >
        
        {/* ═════════════════════════════════════════════════════════════
            LEFT COLUMN: THE 3D FLUID RIBBON HERO
            Styled identically to the left half of the screenshot
            ═════════════════════════════════════════════════════════════ */}
        <div className="relative w-full lg:w-[48%] min-h-[380px] lg:min-h-[660px] flex flex-col justify-between p-8 sm:p-10 lg:p-12 overflow-hidden bg-black shrink-0">
          
          {/* 3D Iridescent Fluid Ribbon Background */}
          <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none">
            <img
              src={authFluidRibbon}
              alt="VerifAI Fluid Ribbon Visual"
              className="w-full h-full object-cover object-center scale-[1.02]"
            />
            {/* Subtle top and bottom dark gradient for optimal text contrast */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-transparent to-black/90 pointer-events-none" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(0,0,0,0.85)_0%,transparent_60%)] pointer-events-none" />
          </div>

          {/* Top Tag: "A WISE QUOTE ——————————" adapted for VerifAI */}
          <div className="relative z-10 flex items-center gap-3">
            <span className="text-[11px] sm:text-xs font-semibold tracking-[0.25em] text-white/90 uppercase">
              {mode === 'signup' ? 'VERIFIED INTELLIGENCE' : 'A WISE QUOTE'}
            </span>
            <div className="h-[1.5px] w-20 sm:w-28 bg-white/70 rounded-full" />
          </div>

          {/* Bottom Editorial Serif Typography & Subtitle */}
          <div className="relative z-10 mt-auto pt-16">
            <AnimatePresence mode="wait">
              {mode === 'signup' ? (
                <motion.div
                  key="quote-signup"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  <h2 className="font-['Playfair_Display',Georgia,serif] text-4xl sm:text-5xl lg:text-[54px] font-normal leading-[1.08] tracking-tight text-white mb-4">
                    Shield<br />
                    Every Claim<br />
                    You Make
                  </h2>
                  <p className="text-white/80 text-xs sm:text-sm font-normal leading-relaxed max-w-sm drop-shadow-sm">
                    Empowering enterprises, researchers, and creators with cryptographic truth and real-time AI fact checking.
                  </p>
                </motion.div>
              ) : mode === 'forgot-password' ? (
                <motion.div
                  key="quote-reset"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  <h2 className="font-['Playfair_Display',Georgia,serif] text-4xl sm:text-5xl lg:text-[54px] font-normal leading-[1.08] tracking-tight text-white mb-4">
                    Restore<br />
                    Your Verified<br />
                    Access
                  </h2>
                  <p className="text-white/80 text-xs sm:text-sm font-normal leading-relaxed max-w-sm drop-shadow-sm">
                    Regain access to your multi-model verification logs, custom API keys, and audit history.
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="quote-login"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Matches the exact visual rhythm of "Get Everything You Want" */}
                  <h2 className="font-['Playfair_Display',Georgia,serif] text-4xl sm:text-5xl lg:text-[54px] font-normal leading-[1.08] tracking-tight text-white mb-4">
                    Verify<br />
                    Everything<br />
                    You See
                  </h2>
                  <p className="text-white/80 text-xs sm:text-sm font-normal leading-relaxed max-w-sm drop-shadow-sm">
                    You can get verified truth when you check the evidence, trust the consensus, and stick to the facts.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* ═════════════════════════════════════════════════════════════
            RIGHT COLUMN: PRISTINE WHITE AUTHENTICATION FORM
            Styled identically to the right half of the screenshot
            ═════════════════════════════════════════════════════════════ */}
        <div className="relative w-full lg:w-[52%] bg-white text-neutral-900 p-8 sm:p-12 lg:p-14 flex flex-col justify-between">
          
          {/* Top Brand Logo: Organic Spiral Mark + "VerifAI" */}
          <div className="flex items-center justify-center gap-2 mb-8">
            {/* Custom SVG Swirl / Ripple Glyph matching screenshot logo */}
            <svg 
              className="w-5 h-5 text-neutral-900 shrink-0" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2.2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M12 2a10 10 0 1 0 10 10" />
              <path d="M12 6a6 6 0 1 0 6 6" />
              <path d="M12 10a2 2 0 1 0 2 2" />
            </svg>
            <span className="text-lg font-semibold tracking-tight text-neutral-900">
              VerifAI
            </span>
          </div>

          {/* Form Content Area */}
          <div className="max-w-[360px] w-full mx-auto my-auto">
            
            {/* Title & Subtitle */}
            <div className="text-center mb-7">
              <h1 className="font-['Playfair_Display',Georgia,serif] text-3xl sm:text-[36px] font-medium tracking-tight text-neutral-900 leading-tight">
                {mode === 'login' && 'Welcome Back'}
                {mode === 'signup' && 'Create Account'}
                {mode === 'forgot-password' && 'Reset Password'}
              </h1>
              <p className="text-xs sm:text-sm text-neutral-500 mt-2 font-normal leading-relaxed">
                {mode === 'login' && 'Enter your email and password to access your account'}
                {mode === 'signup' && 'Enter your details to start verifying claims and models'}
                {mode === 'forgot-password' && 'Enter your email to receive recovery instructions'}
              </p>
            </div>

            {/* Status Feedback Alerts */}
            <AnimatePresence mode="wait">
              {errorMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-start gap-2 shadow-xs text-left"
                >
                  <AlertCircle size={15} className="text-rose-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{errorMessage}</span>
                </motion.div>
              )}

              {successMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-start gap-2 shadow-xs text-left"
                >
                  <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{successMessage}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* ─────────────────────────────────────────────────────────
                VIEW: FORGOT PASSWORD FLOW
                ───────────────────────────────────────────────────────── */}
            {mode === 'forgot-password' ? (
              <form onSubmit={handlePasswordResetSubmit} className="space-y-4">
                <div>
                  <label htmlFor="reset-email" className="block text-xs font-medium text-neutral-800 text-left mb-1.5">
                    Email
                  </label>
                  <input
                    id="reset-email"
                    type="email"
                    value={resetEmail || email}
                    onChange={(e) => {
                      setResetEmail(e.target.value);
                      setEmail(e.target.value);
                    }}
                    placeholder="Enter your email"
                    required
                    autoComplete="email"
                    className="w-full bg-[#f3f4f8] hover:bg-[#ebedf3] focus:bg-white text-neutral-900 text-sm rounded-xl px-4 py-3 border border-transparent focus:border-neutral-300 focus:ring-4 focus:ring-neutral-900/5 transition-all outline-none placeholder:text-neutral-400"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isResetSending}
                  className="w-full bg-black hover:bg-neutral-800 active:scale-[0.99] text-white font-medium text-sm py-3.2 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer mt-2"
                >
                  {isResetSending ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <span>Send Reset Instructions</span>
                  )}
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => switchMode('login')}
                    className="inline-flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-900 font-medium transition-colors cursor-pointer"
                  >
                    <ArrowLeft size={13} />
                    <span>Back to Sign In</span>
                  </button>
                </div>
              </form>
            ) : (
              /* ─────────────────────────────────────────────────────────
                  VIEW: LOGIN & SIGNUP FORMS
                  ───────────────────────────────────────────────────────── */
              <form onSubmit={handleSubmit} className="space-y-3.5">
                
                {/* Full Name (Sign Up only) */}
                {mode === 'signup' && (
                  <div>
                    <label htmlFor="name" className="block text-xs font-medium text-neutral-800 text-left mb-1.5">
                      Full Name
                    </label>
                    <input
                      id="name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter your full name"
                      required
                      autoComplete="name"
                      className="w-full bg-[#f3f4f8] hover:bg-[#ebedf3] focus:bg-white text-neutral-900 text-sm rounded-xl px-4 py-3 border border-transparent focus:border-neutral-300 focus:ring-4 focus:ring-neutral-900/5 transition-all outline-none placeholder:text-neutral-400"
                    />
                  </div>
                )}

                {/* Email Address */}
                <div>
                  <label htmlFor="email" className="block text-xs font-medium text-neutral-800 text-left mb-1.5">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                    autoComplete="email"
                    className="w-full bg-[#f3f4f8] hover:bg-[#ebedf3] focus:bg-white text-neutral-900 text-sm rounded-xl px-4 py-3 border border-transparent focus:border-neutral-300 focus:ring-4 focus:ring-neutral-900/5 transition-all outline-none placeholder:text-neutral-400"
                  />
                </div>

                {/* Password Field */}
                <div>
                  <label htmlFor="password" className="block text-xs font-medium text-neutral-800 text-left mb-1.5">
                    Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      required
                      autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                      className="w-full bg-[#f3f4f8] hover:bg-[#ebedf3] focus:bg-white text-neutral-900 text-sm rounded-xl px-4 py-3 pr-10 border border-transparent focus:border-neutral-300 focus:ring-4 focus:ring-neutral-900/5 transition-all outline-none placeholder:text-neutral-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      className="absolute right-3 text-neutral-400 hover:text-neutral-600 transition-colors p-1 cursor-pointer"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password (Sign Up only) */}
                {mode === 'signup' && (
                  <div>
                    <label htmlFor="confirm-password" className="block text-xs font-medium text-neutral-800 text-left mb-1.5">
                      Confirm Password
                    </label>
                    <div className="relative flex items-center">
                      <input
                        id="confirm-password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Re-enter password"
                        required
                        autoComplete="new-password"
                        className="w-full bg-[#f3f4f8] hover:bg-[#ebedf3] focus:bg-white text-neutral-900 text-sm rounded-xl px-4 py-3 pr-10 border border-transparent focus:border-neutral-300 focus:ring-4 focus:ring-neutral-900/5 transition-all outline-none placeholder:text-neutral-400"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        tabIndex={-1}
                        aria-label={showConfirmPassword ? 'Hide confirmation password' : 'Show confirmation password'}
                        className="absolute right-3 text-neutral-400 hover:text-neutral-600 transition-colors p-1 cursor-pointer"
                      >
                        {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Remember me & Forgot Password Row (Login mode) */}
                {mode === 'login' && (
                  <div className="flex items-center justify-between pt-1">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="w-4 h-4 rounded border-neutral-300 text-black focus:ring-black cursor-pointer accent-black"
                      />
                      <span className="text-xs text-neutral-600">Remember me</span>
                    </label>

                    <button
                      type="button"
                      onClick={() => switchMode('forgot-password')}
                      className="text-xs font-medium text-neutral-700 hover:text-black transition-colors cursor-pointer"
                    >
                      Forgot Password
                    </button>
                  </div>
                )}

                {/* Terms & Conditions Checkbox (Sign Up mode) */}
                {mode === 'signup' && (
                  <div className="pt-1 text-left">
                    <label className="flex items-start gap-2.5 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={agreeTerms}
                        onChange={(e) => {
                          setAgreeTerms(e.target.checked);
                          if (e.target.checked) setConsentError(null);
                        }}
                        className="w-4 h-4 rounded border-neutral-300 text-black focus:ring-black cursor-pointer accent-black mt-0.5 shrink-0"
                      />
                      <span className="text-[11px] text-neutral-600 leading-tight">
                        I agree to the{' '}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setPolicyModalTab('terms');
                            setPolicyModalOpen(true);
                          }}
                          className="font-medium text-neutral-900 underline hover:text-black cursor-pointer"
                        >
                          Terms of Service
                        </button>{' '}
                        and{' '}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setPolicyModalTab('privacy');
                            setPolicyModalOpen(true);
                          }}
                          className="font-medium text-neutral-900 underline hover:text-black cursor-pointer"
                        >
                          Privacy Policy
                        </button>
                      </span>
                    </label>
                    {consentError && (
                      <p className="text-[11px] text-rose-600 mt-1">{consentError}</p>
                    )}
                  </div>
                )}

                {/* Primary Button: Solid Black "Sign In" / "Create Account" */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-black hover:bg-neutral-800 active:scale-[0.99] text-white font-medium text-sm py-3.2 rounded-xl transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isLoading ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
                    )}
                  </button>
                </div>

                {/* Secondary Button: Clean White with Google G Logo */}
                <div>
                  <button
                    type="button"
                    onClick={handleGoogleAuth}
                    disabled={isGoogleLoading}
                    className="w-full bg-white hover:bg-neutral-50 active:scale-[0.99] border border-neutral-200 text-neutral-800 font-medium text-sm py-3 rounded-xl transition-all shadow-xs flex items-center justify-center gap-2.5 cursor-pointer"
                  >
                    {isGoogleLoading ? (
                      <div className="w-4 h-4 border-2 border-neutral-600 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        {/* Official 4-color Google G Icon */}
                        <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                          <path
                            fill="#4285F4"
                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                          />
                          <path
                            fill="#34A853"
                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                          />
                          <path
                            fill="#FBBC05"
                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                          />
                          <path
                            fill="#EA4335"
                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                          />
                        </svg>
                        <span>
                          {mode === 'login' ? 'Sign In with Google' : 'Sign Up with Google'}
                        </span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {/* Bottom Mode Switcher */}
            <div className="text-center mt-7">
              {mode === 'login' ? (
                <p className="text-xs text-neutral-500">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('signup')}
                    className="font-semibold text-neutral-900 hover:underline cursor-pointer ml-0.5"
                  >
                    Sign Up
                  </button>
                </p>
              ) : mode === 'signup' ? (
                <p className="text-xs text-neutral-500">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('login')}
                    className="font-semibold text-neutral-900 hover:underline cursor-pointer ml-0.5"
                  >
                    Sign In
                  </button>
                </p>
              ) : (
                <p className="text-xs text-neutral-500">
                  Remembered your password?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('login')}
                    className="font-semibold text-neutral-900 hover:underline cursor-pointer ml-0.5"
                  >
                    Sign In
                  </button>
                </p>
              )}
            </div>

          </div>

          {/* Bottom Micro Footer */}
          <div className="mt-8 pt-4 text-center">
            <div className="flex items-center justify-center gap-4 text-[11px] text-neutral-400">
              <button
                type="button"
                onClick={() => {
                  setPolicyModalTab('terms');
                  setPolicyModalOpen(true);
                }}
                className="hover:text-neutral-700 transition-colors cursor-pointer"
              >
                Terms
              </button>
              <span>•</span>
              <button
                type="button"
                onClick={() => {
                  setPolicyModalTab('privacy');
                  setPolicyModalOpen(true);
                }}
                className="hover:text-neutral-700 transition-colors cursor-pointer"
              >
                Privacy
              </button>
              <span>•</span>
              <span className="text-neutral-300">v2.4</span>
            </div>
          </div>

        </div>

      </motion.div>

      {/* Accessible Policy Viewer Modal */}
      <PolicyModal
        isOpen={policyModalOpen}
        onClose={() => setPolicyModalOpen(false)}
        initialTab={policyModalTab}
        onAcceptAndClose={() => {
          setAgreeTerms(true);
          setConsentError(null);
        }}
      />

    </div>
  );
};

export const LoginPage: React.FC<SignupPageProps> = (props) => {
  return <SignupPage {...props} initialMode="login" />;
};

export default SignupPage;
