import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, Eye, EyeOff, AtSign, AlertCircle, LoaderCircle, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { ApiError, setAuthToken } from '../api/client';
import { firebaseSignInWithGoogle, firebaseSignOut, formatFirebaseErrorMessage } from '../lib/firebase';
import { PolicyModal, type PolicyTab } from '../components/legal/PolicyModal';
import authIllustration from '../assets/auth-illustration.png';
import './AuthReference.css';

interface SignupPageProps {
  initialMode?: 'signup' | 'login';
  theme?: 'light' | 'dark';
  onAuthSuccess?: (user: { fullName: string; email: string }) => void;
  isAuthenticated?: boolean;
}

type UsernameState = 'idle' | 'invalid' | 'checking' | 'available' | 'taken' | 'error';
const usernamePattern = /^[a-zA-Z0-9_-]{3,64}$/;

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

export const SignupPage: React.FC<SignupPageProps> = ({
  initialMode = 'login', onAuthSuccess, isAuthenticated = false,
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isSignup = location.pathname === '/signup'
    || (location.pathname !== '/login' && initialMode === 'signup');
  const incoming = (location.state as { from?: unknown } | null)?.from;
  const destination = typeof incoming === 'string' &&
    /^\/(dashboard|chat|verify|verification|knowledge-base|history|reports|model-leaderboard|settings)(\/|$)/.test(incoming)
    ? incoming : '/dashboard';

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [usernameState, setUsernameState] = useState<UsernameState>('idle');
  const [checkedUsername, setCheckedUsername] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [pending, setPending] = useState<'password' | 'google' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<'username' | 'email' | null>(null);
  const [policyOpen, setPolicyOpen] = useState(false);
  const [policyTab, setPolicyTab] = useState<PolicyTab>('terms');
  const [completed, setCompleted] = useState(false);
  const errorRef = useRef<HTMLParagraphElement | null>(null);

  useEffect(() => {
    if (isAuthenticated) navigate(destination, { replace: true });
  }, [isAuthenticated, destination, navigate]);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  // Debounced availability is advisory; the unique database index is final.
  useEffect(() => {
    if (!isSignup) return;
    const normalized = username.trim().toLowerCase();
    if (!normalized) {
      setUsernameState('idle');
      setCheckedUsername('');
      return;
    }
    if (!usernamePattern.test(normalized)) {
      setUsernameState('invalid');
      setCheckedUsername('');
      return;
    }
    let active = true;
    setUsernameState('checking');
    setCheckedUsername('');
    const timer = window.setTimeout(() => {
      authApi.checkUsername(normalized)
        .then(result => {
          if (!active) return;
          setCheckedUsername(result.username);
          setUsernameState(result.available ? 'available' : 'taken');
        })
        .catch(() => { if (active) setUsernameState('error'); });
    }, 420);
    return () => { active = false; window.clearTimeout(timer); };
  }, [isSignup, username]);

  const navigateMode = (mode: 'signup' | 'login') => {
    if (pending) return;
    setError(null); setFieldError(null); setPassword(''); setShowPassword(false);
    navigate(mode === 'signup' ? '/signup' : '/login', { state: location.state });
  };

  const onSuccess = (fullName: string, address: string) => {
    setCompleted(true);
    if (onAuthSuccess) onAuthSuccess({ fullName, email: address });
    else navigate(destination, { replace: true });
  };

  const submitPassword = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (pending || completed) return;
    setError(null); setFieldError(null);
    const cleanEmail = email.trim().toLowerCase();
    const cleanUsername = username.trim().toLowerCase();

    if (!cleanEmail || (isSignup && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail))) {
      setFieldError('email');
      setError(isSignup ? 'Enter a valid email address.' : 'Enter your email or username.');
      return;
    }
    if (!password) { setError('Enter your password.'); return; }
    if (isSignup) {
      if (!usernamePattern.test(cleanUsername)) {
        setFieldError('username');
        setError('Choose a username with 3–64 letters, numbers, underscores or hyphens.');
        return;
      }
      if (usernameState === 'taken' && checkedUsername === cleanUsername) {
        setFieldError('username');
        setError('That username is already taken. Choose a different one.');
        return;
      }
      if (password.length < 8 || password.length > 128 ||
          !/[a-zA-Z]/.test(password) || !/\d/.test(password)) {
        setError('Use 8–128 characters, including at least one letter and one number.');
        return;
      }
      if (!termsAccepted) {
        setError('Accept the Terms of Service and Privacy Policy to create an account.');
        return;
      }
    }
    setPending('password');
    let created = false;
    try {
      if (isSignup) {
        await authApi.register({
          username: cleanUsername, email: cleanEmail,
          password, terms_accepted: termsAccepted,
        });
        created = true;
      }
      const result = await authApi.login({ email_or_username: cleanEmail, password });
      if (!result.access_token) throw new Error('Could not establish a secure session.');
      if (!isSignup && !keepSignedIn) setAuthToken(result.access_token, false);
      onSuccess(isSignup ? cleanUsername : cleanEmail.split('@')[0], cleanEmail);
    } catch (err) {
      if (created) {
        setError('Your account was created. Please sign in using your new credentials.');
      } else if (err instanceof ApiError && err.status === 409) {
        const conflictField = err.details?.field === 'email' ? 'email' : 'username';
        setFieldError(conflictField);
        setError(conflictField === 'username'
          ? 'That username is already taken. Please choose another.'
          : 'An account already exists with that email address. Sign in instead.');
        if (conflictField === 'username') setUsernameState('taken');
      } else {
        setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.');
      }
    } finally { setPending(null); }
  };

  const submitGoogle = async () => {
    if (pending || completed) return;
    setError(null); setFieldError(null);
    if (isSignup && !termsAccepted) {
      setError('Accept the Terms of Service and Privacy Policy to create an account.');
      return;
    }
    setPending('google');
    try {
      const result = await firebaseSignInWithGoogle({
        isSignup, termsAccepted: isSignup ? termsAccepted : true,
      });
      if (!result.tokenResponse?.access_token) {
        await firebaseSignOut();
        throw new Error('Google login did not establish a VerifAI session. Please try again.');
      }
      onSuccess(result.displayName || 'Google User', result.email);
    } catch (err) { setError(formatFirebaseErrorMessage(err)); }
    finally { setPending(null); }
  };

  const openPolicy = (tab: PolicyTab) => { setPolicyTab(tab); setPolicyOpen(true); };
  const usernameHint = ({
    idle: '3–64 characters · letters, numbers, _ or -',
    invalid: 'Use 3–64 letters, numbers, underscores or hyphens.',
    checking: 'Checking username availability…',
    available: '@' + checkedUsername + ' is available',
    taken: '@' + (checkedUsername || username.trim().toLowerCase()) + ' is already taken',
    error: 'Availability unavailable; final check happens at signup.',
  } as const)[usernameState];
  const busy = Boolean(pending) || completed;

  return (
    <div className="auth-studio" data-mode={isSignup ? 'signup' : 'login'}>
      <div className="auth-studio__atmosphere" aria-hidden="true"><i/><i/><i/><i/><i/></div>
      <div className="auth-studio__frame">
        <main className="auth-studio__main" aria-labelledby="auth-studio-title">
          <header className="auth-studio__header">
            <a href="/" className="auth-studio__back-link">
              <ArrowLeft size={17} aria-hidden="true"/> <span>Back to website</span>
            </a>
          </header>
          <div className="auth-studio__content">
            <div className="auth-studio__brand-block">
              <div className="auth-studio__brand">
                <a href="/" className="auth-studio__logo" aria-label="VerifAI homepage">
                  <span className="auth-studio__logo-mark"><ShieldCheck size={24}/></span>
                  <span>Verif<span>AI</span></span>
                </a>
                <span className="auth-studio__brand-subline">
                  {isSignup ? 'CREATE YOUR WORKSPACE' : 'WELCOME BACK'}
                </span>
              </div>
            </div>
            <h1 id="auth-studio-title" className="auth-studio__heading">
              {isSignup ? 'Create an account' : 'Log in to VerifAI'}
            </h1>
            <p className="auth-studio__intro">
              Verify content. Validate evidence.<br/>Build a more trustworthy world.
            </p>
            {error && <p role="alert" tabIndex={-1} ref={errorRef} className="auth-studio__error">
              <AlertCircle size={17} aria-hidden="true"/><span>{error}</span>
            </p>}
            <form className="auth-studio__form" onSubmit={submitPassword} noValidate>
              {isSignup && <div className="auth-studio__field">
                <label htmlFor="auth-username">Username</label>
                <div className={'auth-studio__input-wrap ' + (fieldError === 'username' ? 'auth-studio__input-wrap--invalid' : '')}>
                  <AtSign size={18} className="auth-studio__field-icon" aria-hidden="true"/>
                  <input id="auth-username" name="username" type="text"
                    minLength={3} maxLength={64} autoComplete="username" autoCapitalize="none"
                    spellCheck={false} placeholder="Choose your unique username"
                    required value={username} disabled={busy}
                    aria-invalid={fieldError === 'username' || usernameState === 'taken'}
                    aria-describedby="auth-username-help"
                    onChange={e => {setUsername(e.target.value); setFieldError(null); setError(null);}}/>
                  {usernameState === 'checking' && <LoaderCircle size={16} className="auth-studio__check-spin" aria-hidden="true"/>}
                  {usernameState === 'available' && <CheckCircle2 size={18} className="auth-studio__available-icon" aria-hidden="true"/>}
                </div>
                <p id="auth-username-help" role="status"
                  className={'auth-studio__username-hint auth-studio__username-hint--' + usernameState}>
                  {usernameHint}
                </p>
              </div>}
              <div className="auth-studio__field">
                <label htmlFor="auth-email">{isSignup ? 'Email address' : 'Email or username'}</label>
                <div className={'auth-studio__input-wrap ' + (fieldError === 'email' ? 'auth-studio__input-wrap--invalid' : '')}>
                  <AtSign size={18} className="auth-studio__field-icon" aria-hidden="true"/>
                  <input id="auth-email" name="email" type={isSignup ? 'email' : 'text'}
                    autoComplete={isSignup ? 'email' : 'username'} autoCapitalize="none"
                    placeholder={isSignup ? 'you@example.com' : 'Email or username'}
                    required maxLength={255} value={email} disabled={busy}
                    onChange={e => {setEmail(e.target.value); setFieldError(null); setError(null);}}/>
                </div>
              </div>
              <div className="auth-studio__field">
                <label htmlFor="auth-password">Password</label>
                <div className="auth-studio__input-wrap">
                  <LockKeyhole size={18} className="auth-studio__field-icon" aria-hidden="true"/>
                  <input id="auth-password" name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete={isSignup ? 'new-password' : 'current-password'}
                    placeholder={isSignup ? 'Create a secure password' : 'Password'}
                    minLength={isSignup ? 8 : 1} maxLength={128} required
                    value={password} disabled={busy}
                    onChange={e => {setPassword(e.target.value); setError(null);}}/>
                  <button type="button" className="auth-studio__reveal"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    aria-pressed={showPassword} disabled={busy}
                    onClick={() => setShowPassword(v => !v)}>
                    {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                  </button>
                </div>
              </div>
              {!isSignup && <label className="auth-studio__remember">
                <input type="checkbox" checked={keepSignedIn} disabled={busy}
                  onChange={e => setKeepSignedIn(e.target.checked)}/>
                <span>Keep me signed in</span>
              </label>}
              {isSignup && <label className="auth-studio__consent">
                <input type="checkbox" name="accept-policy" checked={termsAccepted}
                  disabled={busy} onChange={e => {setTermsAccepted(e.target.checked); setError(null);}}/>
                <span>I agree to the{' '}
                  <button type="button" onClick={e => {e.preventDefault(); openPolicy('terms');}}>Terms</button>
                  {' '}and{' '}
                  <button type="button" onClick={e => {e.preventDefault(); openPolicy('privacy');}}>Privacy Policy</button>.
                </span>
              </label>}
              <button type="submit" className="auth-studio__submit" disabled={busy}>
                <span>{pending === 'password'
                  ? (isSignup ? 'Creating your account…' : 'Signing you in…')
                  : completed ? 'Opening your dashboard…' : isSignup ? 'Create account' : 'Log in'}</span>
                {pending === 'password'
                  ? <LoaderCircle size={18} className="auth-studio__check-spin" aria-hidden="true"/>
                  : <ArrowRight size={19} aria-hidden="true"/>}
              </button>
            </form>
            <div className="auth-studio__divider"><span>or continue with</span></div>
            <button type="button" className="auth-studio__google" disabled={busy}
              onClick={() => void submitGoogle()}>
              {pending === 'google'
                ? <LoaderCircle size={19} className="auth-studio__check-spin" aria-hidden="true"/>
                : <GoogleIcon/>}
              <span>{pending === 'google' ? 'Connecting…' : 'Continue with Google'}</span>
            </button>
            <div className="auth-studio__account-prompt">
              <p>{isSignup ? 'Already have an account?' : 'New to VerifAI?'}</p>
              <button className="auth-studio__account-action" type="button"
                onClick={() => navigateMode(isSignup ? 'login' : 'signup')} disabled={busy}>
                <span>{isSignup ? 'Sign in to your account' : 'Create your free account'}</span>
                <ArrowRight size={18} aria-hidden="true"/>
              </button>
            </div>
          </div>
        </main>
        <section className="auth-studio__visual" aria-label="Trust and verification illustration">
          <img className="auth-studio__photo"
            src={authIllustration}
            alt="Green verification shield, evidence documents and magnifying glass framed by sculpted white paper"/>
        </section>
      </div>
      <PolicyModal isOpen={policyOpen} initialTab={policyTab}
        onClose={() => setPolicyOpen(false)}
        onAcceptAndClose={() => {setTermsAccepted(true); setError(null);}}/>
    </div>
  );
};

export const LoginPage: React.FC<SignupPageProps> = props => (
  <SignupPage {...props} initialMode="login"/>
);
export default SignupPage;
