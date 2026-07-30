import { createTamagui, createTokens } from 'tamagui';
import { defaultConfig } from '@tamagui/config/v4';
import { mobileTokens } from './theme/tokens';

// Build a shared color palette from both light and dark token sets.
const colorTokens = createTokens({
  color: {
    // light palette
    bg: mobileTokens.light.bg,
    surface: mobileTokens.light.surface,
    surface2: mobileTokens.light.surface2,
    border: mobileTokens.light.border,
    text: mobileTokens.light.text,
    textMuted: mobileTokens.light.textMuted,
    accent: mobileTokens.light.accent,
    accentFg: mobileTokens.light.accentFg,
    statusNew: mobileTokens.light.statusNew,
    statusQualifying: mobileTokens.light.statusQualifying,
    statusHot: mobileTokens.light.statusHot,
    statusBooked: mobileTokens.light.statusBooked,
    statusEscalated: mobileTokens.light.statusEscalated,
    // dark palette
    bgDark: mobileTokens.dark.bg,
    surfaceDark: mobileTokens.dark.surface,
    surface2Dark: mobileTokens.dark.surface2,
    borderDark: mobileTokens.dark.border,
    textDark: mobileTokens.dark.text,
    textMutedDark: mobileTokens.dark.textMuted,
    accentDark: mobileTokens.dark.accent,
    accentFgDark: mobileTokens.dark.accentFg,
    statusBookedDark: mobileTokens.dark.statusBooked,
  },
  // Required by createTokens — inherit from defaultConfig
  size: defaultConfig.tokens.size,
  space: defaultConfig.tokens.space,
  zIndex: defaultConfig.tokens.zIndex,
  radius: defaultConfig.tokens.radius,
});

// v4 `defaultConfig` is a raw config object; createTamagui builds the runtime config.
// No @tamagui/babel-plugin is used (optional; omitting avoids the Expo SDK 56
// babel-preset ordering conflict with react-native-reanimated/plugin).
//
// Relax two v4 defaults so we can pass longhand style props (backgroundColor,
// justifyContent, ...) and raw brand hex values directly on components:
//   - onlyAllowShorthands: false → longhand style props are accepted
//   - allowedStyleValues: false  → arbitrary color/size values (raw hex) allowed
export const tamaguiConfig = createTamagui({
  ...defaultConfig,
  tokens: colorTokens,
  themes: {
    light: {
      background: mobileTokens.light.bg,
      backgroundHover: mobileTokens.light.surface,
      backgroundPress: mobileTokens.light.surface2,
      borderColor: mobileTokens.light.border,
      color: mobileTokens.light.text,
      colorMuted: mobileTokens.light.textMuted,
      accent: mobileTokens.light.accent,
      accentFg: mobileTokens.light.accentFg,
      statusNew: mobileTokens.light.statusNew,
      statusQualifying: mobileTokens.light.statusQualifying,
      statusHot: mobileTokens.light.statusHot,
      statusBooked: mobileTokens.light.statusBooked,
      statusEscalated: mobileTokens.light.statusEscalated,
    },
    dark: {
      background: mobileTokens.dark.bg,
      backgroundHover: mobileTokens.dark.surface,
      backgroundPress: mobileTokens.dark.surface2,
      borderColor: mobileTokens.dark.border,
      color: mobileTokens.dark.text,
      colorMuted: mobileTokens.dark.textMuted,
      accent: mobileTokens.dark.accent,
      accentFg: mobileTokens.dark.accentFg,
      statusNew: mobileTokens.dark.statusNew,
      statusQualifying: mobileTokens.dark.statusQualifying,
      statusHot: mobileTokens.dark.statusHot,
      statusBooked: mobileTokens.dark.statusBooked,
      statusEscalated: mobileTokens.dark.statusEscalated,
    },
  },
  settings: {
    ...defaultConfig.settings,
    onlyAllowShorthands: false,
    allowedStyleValues: false,
  },
});

type Conf = typeof tamaguiConfig;

declare module 'tamagui' {
  interface TamaguiCustomConfig extends Conf {}
}

export default tamaguiConfig;
