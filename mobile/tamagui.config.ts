import { createTamagui } from 'tamagui';
import { defaultConfig } from '@tamagui/config/v4';

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
