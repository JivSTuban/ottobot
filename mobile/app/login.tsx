import React, { useState } from 'react';
import { StyleSheet, KeyboardAvoidingView, Platform, View } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { MotiView, MotiText } from 'moti';
import { useReducedMotion } from 'react-native-reanimated';
import { useSignIn } from '@clerk/clerk-expo';
import { YStack, Input, Button, Text, Spinner } from 'tamagui';

// Design tokens (brand — applied as inline props on Tamagui components)
const TOKENS = {
  bg: '#0f1117',
  accent: '#6366f1',
  accentEnd: '#8b5cf6',
  text: '#f1f5f9',
  muted: '#94a3b8',
  surface: '#1a1d27',
  error: '#ef4444',
} as const;

// Tamagui's Input types `placeholderTextColor` as ColorTokens (theme token strings),
// but we pass a raw brand hex. The value is valid at runtime; cast to satisfy the type.
const mutedPlaceholder = TOKENS.muted as unknown as `$${string}`;

// Spring preset — ease-out settle only, honor reduced motion via caller
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

  const disabled = loading || !isLoaded;

  return (
    <YStack flex={1} backgroundColor={TOKENS.bg}>
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

      {/* Soft indigo glow behind wordmark. Pulses when motion is allowed;
          reduced-motion keeps the design layer static at its rest opacity (0.2). */}
      {reduceMotion ? (
        <View style={[styles.glow, { opacity: 0.2 }]} />
      ) : (
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
        <YStack flex={1} justifyContent="flex-end" paddingHorizontal={20} paddingBottom={48}>
          {/* Wordmark */}
          <MotiText
            style={styles.wordmark}
            {...from(0, { translateY: 26, opacity: 0 })}
          >
            OttoBot
          </MotiText>

          {/* Tagline */}
          <MotiText
            style={styles.tagline}
            {...from(70, { translateY: 16, opacity: 0 })}
          >
            Manage your leads.
          </MotiText>

          {/* Glass card */}
          <MotiView {...from(140, { translateY: 40, opacity: 0 })}>
            <YStack
              backgroundColor="rgba(26,29,39,0.88)"
              borderRadius={20}
              padding={20}
              borderWidth={1}
              borderColor="rgba(99,102,241,0.18)"
              gap={10}
            >
              {/* Email field (Tamagui Input) */}
              <MotiView {...from(210, { translateY: 12, opacity: 0 })}>
                <Input
                  value={email}
                  onChangeText={setEmail}
                  placeholder="Email"
                  // raw hex brand token; Tamagui types placeholderTextColor narrowly as ColorTokens
                  placeholderTextColor={mutedPlaceholder}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="next"
                  onFocus={() => setEmailFocused(true)}
                  onBlur={() => setEmailFocused(false)}
                  aria-label="Email address"
                  backgroundColor={TOKENS.surface}
                  color={TOKENS.text}
                  borderRadius={10}
                  borderWidth={1.5}
                  borderColor={emailFocused ? TOKENS.accent : 'transparent'}
                  height={48}
                  fontSize={15}
                />
              </MotiView>

              {/* Password field (Tamagui Input) */}
              <MotiView {...from(280, { translateY: 12, opacity: 0 })}>
                <Input
                  value={password}
                  onChangeText={setPassword}
                  placeholder="Password"
                  // raw hex brand token; Tamagui types placeholderTextColor narrowly as ColorTokens
                  placeholderTextColor={mutedPlaceholder}
                  secureTextEntry
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={() => setPasswordFocused(false)}
                  aria-label="Password"
                  backgroundColor={TOKENS.surface}
                  color={TOKENS.text}
                  borderRadius={10}
                  borderWidth={1.5}
                  borderColor={passwordFocused ? TOKENS.accent : 'transparent'}
                  height={48}
                  fontSize={15}
                />
              </MotiView>

              {/* Inline error */}
              {error !== null && (
                <Text
                  color={TOKENS.error}
                  fontSize={12}
                  fontWeight="600"
                  role="alert"
                >
                  {error}
                </Text>
              )}

              {/* Gradient CTA (Tamagui Button, transparent, gradient behind) */}
              <MotiView {...from(350, { translateY: 12, opacity: 0 })}>
                <Button
                  onPress={handleLogin}
                  disabled={disabled}
                  aria-label="Log in"
                  height={50}
                  borderRadius={12}
                  marginTop={6}
                  backgroundColor="transparent"
                  borderWidth={0}
                  opacity={disabled ? 0.6 : 1}
                  pressStyle={{ opacity: 0.85, backgroundColor: 'transparent', scale: 0.97 }}
                  overflow="hidden"
                >
                  <LinearGradient
                    colors={[TOKENS.accent, TOKENS.accentEnd]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={StyleSheet.absoluteFill}
                  />
                  {loading ? (
                    <Spinner color={TOKENS.text} />
                  ) : (
                    <Text color={TOKENS.text} fontSize={15} fontWeight="700" letterSpacing={0.3}>
                      Log in
                    </Text>
                  )}
                </Button>
              </MotiView>

              {/* Forgot password link (Tamagui Button, chromeless) */}
              <Button
                chromeless
                onPress={() => {
                  // TODO Phase 07: wire forgot-password flow
                }}
                aria-label="Forgot password"
                height="auto"
                paddingVertical={8}
                marginTop={4}
                backgroundColor="transparent"
                pressStyle={{ backgroundColor: 'transparent', opacity: 0.6, scale: 0.98 }}
              >
                <Text color={TOKENS.muted} fontSize={13}>
                  Forgot password?
                </Text>
              </Button>
            </YStack>
          </MotiView>
        </YStack>
      </KeyboardAvoidingView>
    </YStack>
  );
}

const styles = StyleSheet.create({
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
    // No native blur without expo-blur; approximate the glow with low opacity
    opacity: 0.18,
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
});
