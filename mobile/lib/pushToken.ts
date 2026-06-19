import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  // Push notifications only work on physical devices
  if (!Device.isDevice) {
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') {
    return null;
  }

  // projectId comes from app.json extra.eas.projectId — NOT hardcoded
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  if (!projectId) {
    console.warn('EAS projectId not configured — push token registration skipped');
    return null;
  }
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      sound: 'default',
    });
  }

  return token; // 'ExponentPushToken[xxxxxx]'
}
