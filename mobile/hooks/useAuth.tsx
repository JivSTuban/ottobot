import { useState, useEffect } from 'react';
import { Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession()
      .then(({ data: { session } }) => {
        setSession(session);
        setLoading(false);
      })
      .catch(() => {
        // AsyncStorage failures (e.g. corrupted storage on fresh install)
        // must not leave loading=true indefinitely, causing a blank screen.
        setSession(null);
        setLoading(false);
      });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setLoading(false);
      }
    );

    // Cleanup listener on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return {
    session,
    loading,
    signOut: () => supabase.auth.signOut(),
  };
}
