import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Pressable,
} from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { MotiView, MotiText } from 'moti';
import { useReducedMotion } from 'react-native-reanimated';
import { useSignIn } from '@clerk/clerk-expo';

// Design tokens
const TOKENS = {
  bg: '#0f1117',
  accent: '#6366f1',
  accentEnd: '#8b5cf6',
  text: '#f1f5f9',
  muted: '#94a3b8',
  surface: '#1a1d27',
  error: '#ef4444',
} as const;

// Spring presets — ease-out settle only, honor reduced motion via caller
const SPRING = { type: 'spring' as const, damping: 20, stiffness: 220 };

function useMotionConfig(reduceMotion: boolean) {
  const from = (
    delay: number,
    opts: { translateY?: number; opacity?: number }
  ) => {
    if (reduceMotion) return {};
    return {
      from: {
        opacity: opts.opacity ?? 0,
        translateY: opts.translateY ?? 0,
      },
      animate: { opacity: 1, translateY: 0 },
      transition: { ...SPRING, delay },
    };
  };
  return { from };
}

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  const { signIn, setActive, isLoaded } = useSignIn();
  const reduceMotion = useReducedMotion();
  const { from } = useMotionConfig(reduceMotion ?? false);

  async function handleLogin() {
    if (!isLoaded || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await signIn.create({ identifier: email, password });
      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId });
        // Root layout auth gate redirects to /(tabs)/pipeline
      } else {
        setError('Incorrect email or password. Please try again.');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (
        msg.toLowerCase().includes('fetch') ||
        msg.toLowerCase().includes('network') ||
        msg.toLowerCase().includes('connect')
      ) {
        setError("Can't connect. Check your internet.");
      } else {
        setError('Incorrect email or password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.root}>
      {/* Hero backdrop with Ken-Burns motion */}
      <MotiView
        from={reduceMotion ? undefined : { scale: 1.06, translateY: 0 }}
        animate={reduceMotion ? undefined : { scale: 1.14, translateY: -12 }}
        transition={
          reduceMotion
            ? undefined
            : {
                type: 'timing',
                duration: 6000,
                loop: true,
                repeatReverse: true,
              }
        }
        style={StyleSheet.absoluteFill}
      >
        <Image
          source={require('../assets/login-hero.png')}
          style={StyleSheet.absoluteFill}
          contentFit="cover"
          transition={300}
        />
      </MotiView>

      {/* Dark scrim over lower half */}
      <LinearGradient
        colors={['transparent', 'rgba(15,17,23,0.55)', 'rgba(15,17,23,0.92)', '#0f1117']}
        locations={[0, 0.3, 0.55, 0.78]}
        style={StyleSheet.absoluteFill}
      />

      {/* Radial glow behind wordmark (simulated with a blurred circle) */}
      {!reduceMotion && (
        <MotiView
          from={{ opacity: 0.12 }}
          animate={{ opacity: 0.28 }}
          transition={{ type: 'timing', duration: 2800, loop: true, repeatReverse: true }}
          style={styles.glow}
        />
      )}

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.kavWrapper}
      >
        <View style={styles.content}>
          {/* Wordmark */}
          <MotiText
            style={styles.wordmark}
            {...from(150, { translateY: 26, opacity: 0 })}
          >
            OttoBot
          </MotiText>

          {/* Tagline */}
          <MotiText
            style={styles.tagline}
            {...from(300, { translateY: 16, opacity: 0 })}
          >
            Manage your leads.
          </MotiText>

          {/* Glass card */}
          <MotiView
            style={styles.card}
            {...from(450, { translateY: 40, opacity: 0 })}
          >
            {/* Email field */}
            <MotiView {...from(650, { translateY: 12, opacity: 0 })}>
              <TextInput
                style={[styles.input, emailFocused && styles.inputFocused]}
                placeholder="Email"
                placeholderTextColor={TOKENS.muted}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                onFocus={() => setEmailFocused(true)}
                onBlur={() => setEmailFocused(false)}
                returnKeyType="next"
                accessibilityLabel="Email address"
              />
            </MotiView>

            {/* Password field */}
            <MotiView {...from(750, { translateY: 12, opacity: 0 })}>
              <TextInput
                style={[styles.input, styles.inputLast, passwordFocused && styles.inputFocused]}
                placeholder="Password"
                placeholderTextColor={TOKENS.muted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                onFocus={() => setPasswordFocused(true)}
                onBlur={() => setPasswordFocused(false)}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                accessibilityLabel="Password"
              />
            </MotiView>

            {/* Inline error */}
            {error !== null && (
              <Text style={styles.errorText} accessibilityRole="alert">
                {error}
              </Text>
            )}

            {/* Gradient CTA button */}
            <MotiView {...from(900, { translateY: 12, opacity: 0 })}>
              <TouchableOpacity
                onPress={handleLogin}
                disabled={loading || !isLoaded}
                accessibilityRole="button"
                accessibilityLabel="Log in"
                activeOpacity={0.85}
              >
                <LinearGradient
                  colors={[TOKENS.accent, TOKENS.accentEnd]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.loginButton, (loading || !isLoaded) && styles.loginButtonDisabled]}
                >
                  {loading ? (
                    <ActivityIndicator color={TOKENS.text} />
                  ) : (
                    <Text style={styles.loginButtonText}>Log in</Text>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </MotiView>

            {/* Forgot password link */}
            <Pressable
              style={styles.forgotWrap}
              accessibilityRole="link"
              accessibilityLabel="Forgot password"
              onPress={() => {
                // TODO Phase 07: wire forgot-password flow
              }}
            >
              <Text style={styles.forgotText}>Forgot password?</Text>
            </Pressable>
          </MotiView>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: TOKENS.bg,
  },
  kavWrapper: {
    flex: 1,
  },
  glow: {
    position: 'absolute',
    top: '22%',
    alignSelf: 'center',
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: TOKENS.accent,
    // React Native doesn't support blur natively without expo-blur; approximate with opacity
    opacity: 0.18,
  },
  content: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingHorizontal: 20,
    paddingBottom: 48,
  },
  wordmark: {
    fontSize: 36,
    fontWeight: '700',
    color: TOKENS.text,
    textAlign: 'center',
    letterSpacing: -0.5,
    marginBottom: 6,
  },
  tagline: {
    fontSize: 15,
    fontWeight: '400',
    color: TOKENS.muted,
    textAlign: 'center',
    marginBottom: 28,
  },
  card: {
    backgroundColor: 'rgba(26,29,39,0.88)',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.18)',
  },
  input: {
    backgroundColor: TOKENS.surface,
    color: TOKENS.text,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 15,
    marginBottom: 10,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  inputLast: {
    marginBottom: 0,
  },
  inputFocused: {
    borderColor: TOKENS.accent,
  },
  errorText: {
    fontSize: 12,
    fontWeight: '600',
    color: TOKENS.error,
    marginTop: 10,
  },
  loginButton: {
    minHeight: 50,
    borderRadius: 12,
    marginTop: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: TOKENS.text,
    letterSpacing: 0.3,
  },
  forgotWrap: {
    marginTop: 14,
    alignItems: 'center',
  },
  forgotText: {
    fontSize: 13,
    color: TOKENS.muted,
  },
});
