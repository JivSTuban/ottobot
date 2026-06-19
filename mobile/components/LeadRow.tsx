import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

type LeadStatus = 'new' | 'in-progress' | 'booked' | 'escalated';

interface Lead {
  id: string;
  name: string;
  last_message: string;
  status: LeadStatus;
}

interface LeadRowProps {
  lead: Lead;
  onPress: () => void;
}

const STATUS_BADGE_COLORS: Record<LeadStatus, { bg: string; text: string; label: string }> = {
  new: { bg: '#334155', text: '#94a3b8', label: 'NEW' },
  'in-progress': { bg: '#1e3a5f', text: '#60a5fa', label: 'SA PROSESO' },
  booked: { bg: '#14532d', text: '#4ade80', label: 'NAKA-BOOK' },
  escalated: { bg: '#422006', text: '#fb923c', label: 'ESCALATED' },
};

export function LeadRow({ lead, onPress }: LeadRowProps) {
  const badge = STATUS_BADGE_COLORS[lead.status] ?? STATUS_BADGE_COLORS.new;

  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Lead: ${lead.name}`}
    >
      <View style={styles.leftColumn}>
        <Text style={styles.name}>{lead.name}</Text>
        <Text style={styles.lastMessage} numberOfLines={1}>
          {lead.last_message}
        </Text>
      </View>
      <View style={[styles.badge, { backgroundColor: badge.bg }]}>
        <Text style={[styles.badgeText, { color: badge.text }]}>{badge.label}</Text>
      </View>
      <MaterialIcons name="chevron-right" size={20} color="#64748b" />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: 44,
    backgroundColor: '#1a1d27',
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  leftColumn: {
    flex: 1,
  },
  name: {
    fontSize: 20,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  lastMessage: {
    fontSize: 14,
    color: '#64748b',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
