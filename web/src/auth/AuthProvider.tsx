import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { User } from 'firebase/auth';
import { createUserWithEmailAndPassword, onAuthStateChanged, reload, sendEmailVerification, sendPasswordResetEmail, signInWithEmailAndPassword, signOut, updateProfile } from 'firebase/auth';
import { auth } from '../lib/firebase';
import { request } from '../lib/api';

export type UserProfile = {
  user_id: number;
  name: string;
  username: string;
  email: string;
  role: string;
  role_display: string;
  allowed_pages: string[];
};
type Credentials = { email: string; password: string };
type AuthContextValue = {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  verificationRequired: boolean;
  setupRequired: boolean;
  error: string;
  notice: string;
  clearMessage: () => void;
  signIn: (credentials: Credentials) => Promise<void>;
  signUp: (values: Credentials & { name: string; username: string }) => Promise<void>;
  signOutUser: () => Promise<void>;
  resendVerification: () => Promise<void>;
  refreshVerification: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  completeSetup: (name: string, username: string) => Promise<void>;
  requestRole: (role: string, reason: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const PROFILE_KEY = 'quantdb-pending-profile';

function messageOf(error: unknown) {
  const code = (error as { code?: string })?.code || '';
  const messages: Record<string, string> = {
    'auth/invalid-credential': 'Email or password is incorrect.',
    'auth/email-already-in-use': 'An account with this email already exists. Sign in instead.',
    'auth/weak-password': 'Choose a password with at least 8 characters.',
    'auth/invalid-email': 'Enter a valid email address.',
    'auth/too-many-requests': 'Too many attempts. Please wait a few minutes and try again.',
    'auth/network-request-failed': 'Network issue. Check your connection and try again.',
  };
  return messages[code] || (error instanceof Error ? error.message.replace(/^Firebase: /, '') : 'Something went wrong. Please try again.');
}

async function fetchProfile(user: User, forced?: { name: string; username: string }) {
  await user.getIdToken(true);
  try {
    return await request<UserProfile>('/auth/me');
  } catch (error) {
    const isMissing = error instanceof Error && (error.message.includes('profile is not set up') || error.message.includes('403'));
    if (!isMissing) throw error;
    const saved = forced || (() => {
      try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); } catch { return null; }
    })();
    const payload = saved || {
      name: user.displayName || user.email?.split('@')[0] || 'QuantDB Member',
      username: (user.email?.split('@')[0] || 'user').replace(/[^A-Za-z0-9_]/g, '_').slice(0, 30),
    };
    return request<UserProfile>('/auth/sync', { method: 'POST', body: JSON.stringify(payload) });
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const lastUid = useRef<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [verificationRequired, setVerificationRequired] = useState(false);
  const [setupRequired, setSetupRequired] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const resolveUser = useCallback(async (next: User | null) => {
    setUser(next);
    setProfile(null);
    setVerificationRequired(false);
    setSetupRequired(false);
    if (!next) return;
    try {
      const nextProfile = await fetchProfile(next);
      setProfile(nextProfile);
      localStorage.removeItem(PROFILE_KEY);
    } catch (cause) {
      const text = messageOf(cause);
      if (text.includes('Finish setting up') || text.includes('profile is not set up')) setSetupRequired(true);
      else setError(text);
    }
  }, []);

  useEffect(() => onAuthStateChanged(auth, async (next) => {
    if (lastUid.current !== (next?.uid || null)) queryClient.clear();
    lastUid.current = next?.uid || null;
    setLoading(true);
    setError('');
    await resolveUser(next);
    setLoading(false);
  }), [queryClient, resolveUser]);

  const signIn = async ({ email, password }: Credentials) => {
    setError(''); setNotice('');
    const result = await signInWithEmailAndPassword(auth, email.trim(), password);
    const next = await fetchProfile(result.user);
    setUser(result.user); setProfile(next); setVerificationRequired(false); setSetupRequired(false);
    localStorage.removeItem(PROFILE_KEY);
  };

  const signUp = async ({ email, password, name, username }: Credentials & { name: string; username: string }) => {
    setError(''); setNotice('');
    if (!/^[A-Za-z0-9_]{3,30}$/.test(username)) throw new Error('Username must be 3–30 characters: letters, numbers, and underscores only.');
    const result = await createUserWithEmailAndPassword(auth, email.trim(), password);
    await updateProfile(result.user, { displayName: name.trim() });
    localStorage.setItem(PROFILE_KEY, JSON.stringify({ name: name.trim(), username: username.trim() }));
    try {
      const next = await fetchProfile(result.user, { name: name.trim(), username: username.trim() });
      setUser(result.user); setProfile(next); setVerificationRequired(false); setSetupRequired(false);
      localStorage.removeItem(PROFILE_KEY);
    } catch {
      setUser(result.user); setVerificationRequired(false); setSetupRequired(false);
    }
  };

  const resendVerification = async () => {
    if (!auth.currentUser) throw new Error('Sign in to resend the verification email.');
    await sendEmailVerification(auth.currentUser);
    setNotice(`A new verification email was sent to ${auth.currentUser.email}.`);
  };

  const refreshVerification = async () => {
    if (!auth.currentUser) return;
    await reload(auth.currentUser);
    const refreshed = auth.currentUser;
    setUser(refreshed);
    try {
      const next = await fetchProfile(refreshed);
      setProfile(next); setVerificationRequired(false); setSetupRequired(false); setNotice('Welcome to QuantDB.');
      localStorage.removeItem(PROFILE_KEY);
    } catch (cause) {
      if (messageOf(cause).includes('Finish setting up')) setSetupRequired(true);
      else setError(messageOf(cause));
    }
  };

  const completeSetup = async (name: string, username: string) => {
    if (!auth.currentUser?.emailVerified) throw new Error('Verify your email before completing your profile.');
    if (!/^[A-Za-z0-9_]{3,30}$/.test(username)) throw new Error('Username must be 3–30 characters: letters, numbers, and underscores only.');
    const next = await request<UserProfile>('/auth/sync', { method: 'POST', body: JSON.stringify({ name: name.trim(), username: username.trim() }) });
    setProfile(next); setSetupRequired(false); localStorage.removeItem(PROFILE_KEY);
  };

  const requestRole = async (requestedRole: string, reason: string) => {
    await request('/auth/role-request', { method: 'POST', body: JSON.stringify({ requested_role: requestedRole, reason }) });
    setNotice('Role request submitted. An administrator will review it.');
    await queryClient.invalidateQueries({ queryKey: ['my-role-request'] });
  };

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email.trim());
    setNotice(`Password reset link sent to ${email.trim()}.`);
  };
  const signOutUser = async () => {
    setProfile(null); setSetupRequired(false); setVerificationRequired(false); setError('');
    queryClient.clear();
    await signOut(auth);
  };
  const clearMessage = () => { setError(''); setNotice(''); };
  const value = useMemo(() => ({ user, profile, loading, verificationRequired, setupRequired, error, notice, clearMessage, signIn, signUp, signOutUser, resendVerification, refreshVerification, resetPassword, completeSetup, requestRole }), [user, profile, loading, verificationRequired, setupRequired, error, notice]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider.');
  return context;
}
