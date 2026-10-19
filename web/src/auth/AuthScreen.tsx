import { useState } from 'react';
import { Activity, ArrowRight, BadgeCheck, BarChart3, Eye, EyeOff, KeyRound, LockKeyhole, Mail, RefreshCw, ShieldCheck, TrendingUp } from 'lucide-react';
import { useAuth } from './AuthProvider';
import { CandleScene } from './CandleScene';

type Mode = 'signin' | 'signup';

export function AuthScreen() {
  const auth = useAuth();
  const [mode, setMode] = useState<Mode>('signin');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState('');
  const [showReset, setShowReset] = useState(false);

  const run = async (action: () => Promise<void>) => {
    setBusy(true); setFormError(''); auth.clearMessage();
    try { await action(); } catch (cause) { setFormError(cause instanceof Error ? cause.message.replace(/^API \d+: /, '') : 'Please try again.'); }
    finally { setBusy(false); }
  };

  if (auth.verificationRequired) return <div className="auth-page"><div className="auth-glow"/><div className="auth-card verify-card">
    <Brand/>
    <div className="verify-icon"><Mail size={26}/></div>
    <div className="auth-eyebrow">ONE QUICK STEP</div><h1>Verify your email</h1>
    <p className="auth-subtitle">We sent a secure verification link to <strong>{auth.user?.email}</strong>. Open the message and verify your address to continue. If it is missing, check Spam or Promotions.</p>
    {auth.error && !auth.error.includes('API 503: Firebase Admin') && <div className="auth-message is-error">{auth.error}</div>}
    {auth.error.includes('API 503: Firebase Admin') && <div className="auth-message is-error">Your email is verified, but the API cannot connect your account yet. The project administrator must configure the Firebase Admin service account and database access on the API host.</div>}
    {auth.notice && <div className="auth-message">{auth.notice}</div>}
    <button className="auth-submit" disabled={busy} onClick={() => run(auth.refreshVerification)}><BadgeCheck size={17}/> I’ve verified my email <ArrowRight size={16}/></button>
    <button className="auth-secondary" disabled={busy} onClick={() => run(auth.resendVerification)}><RefreshCw size={15}/> Resend verification email</button>
    <button className="auth-text-button" onClick={() => void auth.signOutUser()}>Use a different account</button>
  </div></div>;

  if (auth.setupRequired) return <div className="auth-page"><div className="auth-glow"/><form className="auth-card" onSubmit={(event) => { event.preventDefault(); void run(() => auth.completeSetup(name || auth.user?.displayName || '', username)); }}>
    <Brand/><div className="auth-eyebrow">PROFILE SETUP</div><h1>Welcome to QuantDB</h1>
    <p className="auth-subtitle">Your verified identity is ready. Add the name and username shown in your workspace.</p>
    {(auth.notice || auth.error || formError) && <div className={`auth-message ${auth.error || formError ? 'is-error' : ''}`}>{formError || auth.error || auth.notice}</div>}
    <label className="auth-field">Display name<input required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name"/></label>
    <label className="auth-field">Username<input required minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="your_username"/></label>
    <button className="auth-submit" disabled={busy}>Complete setup <ArrowRight size={16}/></button>
    <button type="button" className="auth-text-button" onClick={() => void auth.signOutUser()}>Sign out</button>
  </form></div>;

  return <main className="auth-page">
    <CandleScene />
    <div className="auth-glow"/>
    <section className="auth-story">
      <Brand/>
      <div className="story-pill"><span className="status-dot"/> QUANTITATIVE FINANCE · RESEARCH TERMINAL</div>
      <h1>Research markets.<br/><span>Test every thesis.</span></h1>
      <p>One focused workspace for market research, portfolio simulation, strategy design and risk analytics.</p>
      <div className="story-dashboard">
        <div className="story-chart-heading"><div><small>QUANTDB RESEARCH</small><strong>From market data to tested strategy</strong></div><span><TrendingUp size={14}/></span></div>
        <div className="story-chart"><svg viewBox="0 0 480 112" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="story-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#0dbbd3" stopOpacity=".28"/><stop offset="1" stopColor="#0dbbd3" stopOpacity="0"/></linearGradient></defs><path d="M0 91 C22 86 31 99 50 76 S79 85 96 65 S120 74 144 59 S166 69 188 45 S217 57 241 43 S265 52 287 33 S316 52 342 27 S366 39 391 21 S420 32 442 13 S463 19 480 4 V112 H0Z" fill="url(#story-fill)"/><path d="M0 91 C22 86 31 99 50 76 S79 85 96 65 S120 74 144 59 S166 69 188 45 S217 57 241 43 S265 52 287 33 S316 52 342 27 S366 39 391 21 S420 32 442 13 S463 19 480 4" fill="none" stroke="#0dbbd3" strokeWidth="2.5"/></svg></div>
        <div className="story-chart-foot"><span><i/> EQUITY CURVE</span><span>SIMULATION · PAPER ONLY</span></div>
      </div>
      <div className="story-features"><span><BarChart3 size={16}/> Market data & analytics</span><span><Activity size={16}/> Paper trading</span><span><ShieldCheck size={16}/> Role based access</span></div>
    </section>

    <section className="auth-panel-wrap"><div className="auth-card">
      <div className="auth-mobile-brand"><Brand/></div>
      <div className="auth-eyebrow"><LockKeyhole size={14}/> SECURE ACCESS GATEWAY</div>
      <h2>{showReset ? 'Reset your password' : mode === 'signin' ? 'Welcome back' : 'Create your account'}</h2>
      <p className="auth-subtitle">{showReset ? 'We’ll email you a secure password reset link.' : mode === 'signin' ? 'Sign in to continue to your QuantDB workspace.' : 'Get started with your verified research account.'}</p>
      {!showReset && <div className="auth-tabs"><button className={mode === 'signin' ? 'selected' : ''} onClick={() => { setMode('signin'); setFormError(''); }}>Sign in</button><button className={mode === 'signup' ? 'selected' : ''} onClick={() => { setMode('signup'); setFormError(''); }}>Create account</button></div>}
      {(formError || auth.error || auth.notice) && <div className={`auth-message ${formError || auth.error ? 'is-error' : ''}`}>{formError || auth.error || auth.notice}</div>}
      <form onSubmit={(event) => { event.preventDefault(); if (showReset) void run(() => auth.resetPassword(email)); else if (mode === 'signin') void run(() => auth.signIn({ email, password })); else void run(() => auth.signUp({ email, password, name, username })); }}>
        {mode === 'signup' && !showReset && <>
          <label className="auth-field">Full name<input autoComplete="name" required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Darshil Prajapati"/></label>
          <label className="auth-field">Username<input autoComplete="username" required minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="3–30 characters"/></label>
        </>}
        <label className="auth-field">Email address<input autoComplete="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"/></label>
        {!showReset && <label className="auth-field">Password<div className="password-wrap"><input autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} type={showPassword ? 'text' : 'password'} minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters"/><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17}/> : <Eye size={17}/>}</button></div></label>}
        {mode === 'signin' && !showReset && <button type="button" className="forgot-link" onClick={() => { setShowReset(true); setFormError(''); }}>Forgot password?</button>}
        <button className="auth-submit" disabled={busy}>{busy ? <span className="spinner"/> : showReset ? <Mail size={16}/> : mode === 'signin' ? <KeyRound size={16}/> : <ShieldCheck size={16}/>} {busy ? 'Please wait…' : showReset ? 'Send reset link' : mode === 'signin' ? 'Sign in securely' : 'Create verified account'} <ArrowRight size={16}/></button>
      </form>
      {showReset && <button className="auth-text-button" onClick={() => { setShowReset(false); setFormError(''); }}>Back to sign in</button>}
      <div className="auth-assurance"><ShieldCheck size={15}/><span>Email verification required · Your role is assigned by the QuantDB administrator.</span></div>
    </div><div className="auth-copyright">QUANTDB RESEARCH TERMINAL <span>·</span> ACADEMIC SIMULATION</div></section>
  </main>;
}

function Brand() { return <div className="auth-brand"><span className="auth-brand-mark">Q</span><span>QUANT<span>DB</span><small>FINANCE & SIMULATION</small></span></div>; }
