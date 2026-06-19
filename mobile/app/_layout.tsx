import { useEffect } from 'react';
import { Stack, Redirect } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useAuth } from '../hooks/useAuth';
import { registerForPushNotificationsAsync } from '../lib/pushToken';
import { supabase } from '../lib/supabase';

export default function RootLayout() {
  const { session, loading } = useAuth();

  useEffect(() => {
    if (!session || loading) return;

    // Register for push notifications after login; failure must NOT crash the app
    (async () => {
      try {
        const token = await registerForPushNotificationsAsync();
        if (token) {
          const apiUrl = process.env.EXPO_PUBLIC_API_URL;
          await fetch(`${apiUrl}/push/send`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`,
            },
            body: JSON.stringify({ expo_token: token }),
          });
        }
      } catch (error) {
        // Push token registration failure is non-fatal — app continues without push
        console.error('Push token registration failed:', error);
      }
    })();
  }, [session, loading]);

  // Show nothing while loading auth state (splash-screen)
  if (loading) {
    return null;
  }

  // Redirect unauthenticated users to login
  if (!session) {
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
