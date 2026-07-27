import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface Message {
  content: string;
  sender: 'agent' | 'lead';
  created_at: string;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAgent = message.sender === 'agent';
  const timestamp = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <View style={[styles.outerView, isAgent ? styles.agentAlign : styles.leadAlign]}>
      <View style={[styles.bubble, isAgent ? styles.agentBubble : styles.leadBubble]}>
        <Text style={styles.content}>{message.content}</Text>
        <Text style={styles.timestamp}>{timestamp}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outerView: {
    marginVertical: 4,
    paddingHorizontal: 16,
  },
  agentAlign: {
    // Agent = outbound (our side) → right, per UAT test 9
    alignItems: 'flex-end',
  },
  leadAlign: {
    // Lead = inbound → left
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '75%',
    borderRadius: 8,
    padding: 8,
  },
  agentBubble: {
    backgroundColor: '#1a1d27',
  },
  leadBubble: {
    backgroundColor: '#2d2f3e',
  },
  content: {
    fontSize: 14,
    color: '#f1f5f9',
  },
  timestamp: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'right',
    marginTop: 2,
  },
});
