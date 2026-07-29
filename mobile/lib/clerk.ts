import * as SecureStore from 'expo-secure-store';
import type { TokenCache } from '@clerk/clerk-expo';

export const tokenCache: TokenCache = {
  async getToken(key) {
    try { return await SecureStore.getItemAsync(key); } catch { return null; }
  },
  async saveToken(key, value) {
    try { await SecureStore.setItemAsync(key, value); } catch {}
  },
};

export const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY!;
