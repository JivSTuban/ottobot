import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useAuth } from '../../hooks/useAuth';

interface DaySlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_open: boolean;
}

const DAYS = [
  { label: 'Lunes', day: 1 },
  { label: 'Martes', day: 2 },
  { label: 'Miyerkules', day: 3 },
  { label: 'Huwebes', day: 4 },
  { label: 'Biyernes', day: 5 },
  { label: 'Sabado', day: 6 },
  { label: 'Linggo', day: 0 },
];

const DEFAULT_SLOTS: DaySlot[] = DAYS.map((d) => ({
  day_of_week: d.day,
  start_time: '09:00',
  end_time: '17:00',
  is_open: d.day >= 1 && d.day <= 5,
}));

export default function SettingsScreen() {
  const { session } = useAuth();
  const [slots, setSlots] = useState<DaySlot[]>(DEFAULT_SLOTS);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchAvailability() {
    if (!session?.access_token || !session?.user?.id) return;
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/availability/${session.user.id}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );
      if (!response.ok) return;
      const json = await response.json();
      const fetchedSlots: DaySlot[] = json.slots ?? [];
      // Merge fetched slots into defaults — a slot in response means is_open: true
      setSlots(
        DEFAULT_SLOTS.map((defaultSlot) => {
          const match = fetchedSlots.find(
            (s) => s.day_of_week === defaultSlot.day_of_week
          );
          return match ? { ...defaultSlot, ...match, is_open: true } : defaultSlot;
        })
      );
    } catch {
      // Non-fatal — keep defaults
    }
  }

  function toggleDay(day_of_week: number) {
    setSlots((prev) =>
      prev.map((slot) =>
        slot.day_of_week === day_of_week
          ? { ...slot, is_open: !slot.is_open }
          : slot
      )
    );
  }

  async function saveAvailability() {
    if (!session?.access_token || !session?.user?.id) return;
    setError(null);
    setSaving(true);
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/availability`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            business_id: session.user.id,
            slots: slots.filter((s) => s.is_open),
          }),
        }
      );
      if (!response.ok) {
        setError('Hindi makakonekta. Tingnan ang internet mo.');
        return;
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError('Hindi makakonekta. Tingnan ang internet mo.');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    fetchAvailability();
  }, [session]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Availability</Text>

      {DAYS.map(({ label, day }) => {
        const slot = slots.find((s) => s.day_of_week === day);
        const isOpen = slot?.is_open ?? false;
        return (
          <TouchableOpacity
            key={day}
            style={styles.dayRow}
            onPress={() => toggleDay(day)}
            accessibilityRole="button"
            accessibilityLabel={`${label} toggle`}
            accessibilityState={{ selected: isOpen }}
          >
            <Text style={styles.dayLabel}>{label}</Text>
            <View
              style={[
                styles.toggle,
                { backgroundColor: isOpen ? '#6366f1' : '#334155' },
              ]}
            />
          </TouchableOpacity>
        );
      })}

      {saved && (
        <Text style={styles.savedText}>Na-save na ang availability mo.</Text>
      )}

      {error && <Text style={styles.errorText}>{error}</Text>}

      <TouchableOpacity
        style={[styles.saveButton, saving && styles.saveButtonSaving]}
        onPress={saveAvailability}
        disabled={saving}
        accessibilityRole="button"
        accessibilityLabel="I-save"
      >
        {saving ? (
          <ActivityIndicator color="#f1f5f9" />
        ) : (
          <Text style={styles.saveButtonText}>I-save</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1117',
  },
  content: {
    paddingBottom: 32,
  },
  heading: {
    fontSize: 20,
    fontWeight: '600',
    color: '#f1f5f9',
    padding: 16,
  },
  dayRow: {
    minHeight: 44,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#1a1d27',
    marginBottom: 1,
  },
  dayLabel: {
    fontSize: 14,
    color: '#f1f5f9',
  },
  toggle: {
    width: 24,
    height: 24,
    borderRadius: 12,
  },
  savedText: {
    fontSize: 14,
    color: '#4ade80',
    textAlign: 'center',
    padding: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    padding: 16,
  },
  saveButton: {
    backgroundColor: '#6366f1',
    minHeight: 44,
    marginHorizontal: 16,
    marginTop: 24,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveButtonSaving: {
    backgroundColor: '#4b4d8c',
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
});
