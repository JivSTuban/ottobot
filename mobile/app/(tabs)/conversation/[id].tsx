import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../../hooks/useAuth';
import { MessageBubble } from '../../../components/MessageBubble';

interface Message {
  id: string;
  content: string;
  sender: 'agent' | 'lead';
  created_at: string;
}

interface LeadDetail {
  id: string;
  name: string;
  status: string;
}

export default function ConversationScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!session?.access_token || !id) return;
    setError(null);
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/leads/${id}/messages`,
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
      setLead(json.lead ?? null);
      // Sort descending by created_at (newest first for inverted FlatList)
      // Map API role field to sender field expected by MessageBubble (WR-05)
      const sorted: Message[] = (json.messages ?? []).map((m: any) => ({
        ...m,
        sender: m.role === 'assistant' ? 'agent' : 'lead',
      })).sort(
        (a: Message, b: Message) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setMessages(sorted);
    } catch {
      setError('Hindi makakonekta. Tingnan ang internet mo.');
    } finally {
      setLoading(false);
    }
  }, [session, id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <View style={styles.container}>
      {lead?.status === 'escalated' && (
        <View style={styles.escalationBanner}>
          <Text style={styles.escalationText}>HOT LEAD — Tawagan na!</Text>
        </View>
      )}

      {error && <Text style={styles.errorText}>{error}</Text>}

      {loading ? (
        <ActivityIndicator color="#6366f1" style={styles.loader} />
      ) : (
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <MessageBubble message={item} />}
          inverted={true}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>Walang mensahe pa.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f1117',
  },
  escalationBanner: {
    backgroundColor: '#ef4444',
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  escalationText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#f1f5f9',
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    padding: 16,
  },
  loader: {
    marginTop: 32,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
  },
});
