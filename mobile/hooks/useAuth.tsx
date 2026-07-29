import { useAuth as useClerkAuth } from '@clerk/clerk-expo';

export function useAuth() {
  const { isSignedIn, isLoaded, getToken, signOut } = useClerkAuth();
  return {
    isSignedIn: !!isSignedIn,
    loading: !isLoaded,
    getToken: () => getToken(),
    signOut: () => signOut(),
  };
}
