import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { supabase } from '../lib/supabase';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  async function handleLogin() {
    setLoading(true);
    setError(null);
    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (authError) {
        const msg = authError.message ?? '';
        if (msg.toLowerCase().includes('fetch') || msg.toLowerCase().includes('network')) {
          setError('Hindi makakonekta. Tingnan ang internet mo.');
        } else {
          setError('Mali ang email o password. Subukan ulit.');
        }
      }
      // On success, root layout auth guard redirects to /(tabs)/pipeline
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '';
      if (msg.toLowerCase().includes('fetch') || msg.toLowerCase().includes('network')) {
        setError('Hindi makakonekta. Tingnan ang internet mo.');
      } else {
        setError('Mali ang email o password. Subukan ulit.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.wordmark}>OttoBot</Text>
      <Text style={styles.tagline}>I-manage ang iyong mga leads.</Text>

      <TextInput
        style={[styles.input, emailFocused && styles.inputFocused]}
        placeholder="Email"
        placeholderTextColor="#64748b"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        onFocus={() => setEmailFocused(true)}
        onBlur={() => setEmailFocused(false)}
      />

      <TextInput
        style={[styles.input, passwordFocused && styles.inputFocused, styles.inputPassword]}
        placeholder="Password"
        placeholderTextColor="#64748b"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={true}
        onFocus={() => setPasswordFocused(true)}
        onBlur={() => setPasswordFocused(false)}
      />

      {error !== null && (
        <Text style={styles.errorText}>{error}</Text>
      )}

      <TouchableOpacity
        style={[styles.loginButton, loading && styles.loginButtonLoading]}
        onPress={handleLogin}
        disabled={loading}
        accessibilityRole="button"
        accessibilityLabel="Mag-login"
      >
        {loading ? (
          <ActivityIndicator color="#f1f5f9" />
        ) : (
          <Text style={styles.loginButtonText}>Mag-login</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1117',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  wordmark: {
    fontSize: 28,
    fontWeight: '600',
    color: '#f1f5f9',
    textAlign: 'center',
  },
  tagline: {
    fontSize: 14,
    fontWeight: '400',
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 32,
    marginTop: 8,
  },
  input: {
    backgroundColor: '#1a1d27',
    color: '#f1f5f9',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  inputFocused: {
    borderColor: '#6366f1',
  },
  inputPassword: {
    marginBottom: 0,
  },
  errorText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ef4444',
    marginTop: 8,
  },
  loginButton: {
    backgroundColor: '#6366f1',
    minHeight: 44,
    borderRadius: 8,
    marginTop: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginButtonLoading: {
    backgroundColor: '#4b4d8c',
  },
  loginButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
});
