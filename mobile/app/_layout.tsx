import { useEffect } from 'react';
import { Stack, Redirect } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ClerkProvider, ClerkLoaded, useAuth } from '@clerk/clerk-expo';
import { CLERK_PUBLISHABLE_KEY, tokenCache } from '../lib/clerk';
import { registerForPushNotificationsAsync } from '../lib/pushToken';

function Gate() {
  const { isSignedIn, isLoaded, getToken } = useAuth();

  useEffect(() => {
    if (!isSignedIn || !isLoaded) return;

    // Register for push notifications after login; failure must NOT crash the app
    (async () => {
      try {
        const token = await registerForPushNotificationsAsync();
        if (token) {
          const apiUrl = process.env.EXPO_PUBLIC_API_URL;
          const bearer = await getToken();
          await fetch(`${apiUrl}/push/send`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${bearer}`,
            },
            body: JSON.stringify({ expo_token: token }),
          });
        }
      } catch (error) {
        // Push token registration failure is non-fatal — app continues without push
        console.error('Push token registration failed:', error);
      }
    })();
  }, [isSignedIn, isLoaded]);

  // Show nothing while loading auth state (splash-screen)
  if (!isLoaded) {
    return null;
  }

  // Redirect unauthenticated users to login
  if (!isSignedIn) {
    return <Redirect href="/login" />;
  }

  return (
    <SafeAreaProvider>
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#0f1117' },
          headerTintColor: '#f1f5f9',
          contentStyle: { backgroundColor: '#0f1117' },
        }}
      >
        <Stack.Screen name="login" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </SafeAreaProvider>
  );
}

export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={tokenCache}>
      <ClerkLoaded><Gate /></ClerkLoaded>
    </ClerkProvider>
  );
}
