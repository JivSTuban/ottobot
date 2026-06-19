import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  SectionList,
  RefreshControl,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../hooks/useAuth';
import { LeadRow } from '../../components/LeadRow';

type LeadStatus = 'new' | 'in-progress' | 'booked' | 'escalated';

interface Lead {
  id: string;
  name: string;
  last_message: string;
  status: LeadStatus;
}

const STATUS_ORDER: LeadStatus[] = ['new', 'in-progress', 'booked', 'escalated'];

const LABEL_MAP: Record<LeadStatus, string> = {
  new: 'NEW',
  'in-progress': 'SA PROSESO',
  booked: 'NAKA-BOOK',
  escalated: 'ESCALATED',
};

export default function PipelineScreen() {
  const router = useRouter();
  const { session } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = useCallback(async () => {
    if (!session?.access_token) return;
    setError(null);
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/leads`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );
      if (!response.ok) {
        setError('Hindi makakonekta. Tingnan ang internet mo.');
        return;
      }
      const json = await response.json();
      setLeads(json.leads ?? []);
    } catch {
      setError('Hindi makakonekta. Tingnan ang internet mo.');
    }
  }, [session]);

  async function handleRefresh() {
    setRefreshing(true);
    await fetchLeads();
    setRefreshing(false);
  }

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  const sections = STATUS_ORDER
    .map((status) => {
      const data = leads.filter((l) => l.status === status);
      return {
        title: `${LABEL_MAP[status]} · ${data.length}`,
        data,
      };
    })
    .filter((s) => s.data.length > 0);

  return (
    <View style={styles.container}>
      {error && <Text style={styles.errorText}>{error}</Text>}
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <LeadRow
            lead={item}
            onPress={() => router.push(`/conversation/${item.id}` as never)}
          />
        )}
        renderSectionHeader={({ section }) => (
          <Text style={styles.sectionHeader}>{section.title}</Text>
        )}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#6366f1"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyTitle}>Wala pang leads</Text>
            <Text style={styles.emptySubtitle}>
              Mag-ingat — kapag may nagmessage, lalabas sila dito.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1117',
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748b',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#0f1117',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#f1f5f9',
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginTop: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    padding: 16,
  },
});
