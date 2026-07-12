import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "../lib/supabase";
import { getMyProfile, createMyProfile, updateMyProfile } from "../lib/api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      if (data.session) loadProfile();
      setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      if (s) loadProfile();
      else setProfile(null);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  async function loadProfile() {
    try {
      const p = await getMyProfile();
      setProfile(p);
      return p;
    } catch {
      setProfile(null);
      return null;
    }
  }

  async function signUp({ email, password, fullName, userType }) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName, user_type: userType } },
    });
    if (error) throw error;

    if (data.session) {
      try {
        await createMyProfile(fullName);
      } catch (err) {
        if (err?.response?.status !== 409) console.error("createMyProfile:", err);
      }
      try {
        const updated = await updateMyProfile({ user_type: userType });
        setProfile(updated);
      } catch {
        try { setProfile(await getMyProfile()); } catch { setProfile(null); }
      }
    }
    return data;
  }

  async function signIn({ email, password }) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    const p = await loadProfile();
    return { ...data, profile: p };
  }

  async function signOut() {
    await supabase.auth.signOut();
    setProfile(null);
  }

  const value = {
    session,
    user: session?.user ?? null,
    profile,
    loading,
    signUp,
    signIn,
    signOut,
    reloadProfile: loadProfile,
  };

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}
