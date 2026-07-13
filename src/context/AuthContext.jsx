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
      setProfile(await getMyProfile());
    } catch {
      // 404 → the user has a Supabase account but no profile row yet.
      // The UI can route them to a "finish your profile" step.
      setProfile(null);
    }
  }

  // signUp → create the profile row (keyed to the Supabase user id) → set role.
  // POST /profiles/me only takes full_name, so user_type goes in a follow-up PATCH.
  async function signUp({ email, password, fullName, userType }) {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;

    // If "Confirm email" is ON in Supabase, there's no session yet — we can't
    // create the profile until the user confirms and signs in. For the sprint,
    // turn that setting off so this runs immediately.
    if (data.session) {
      await createMyProfile(fullName);
      const updated = await updateMyProfile({ user_type: userType });
      setProfile(updated);
    }
    return data;
  }

  async function signIn({ email, password }) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    await loadProfile();
    return data;
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
