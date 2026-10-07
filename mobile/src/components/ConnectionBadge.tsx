import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ConnectionStatus } from '../types/lead';

interface Props {
  status: ConnectionStatus;
}

export const ConnectionBadge: React.FC<Props> = ({ status }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: '#10B981',
          bg: '#D1FAE5',
          text: 'Connected (Live)',
        };
      case 'connecting':
        return {
          color: '#F59E0B',
          bg: '#FEF3C7',
          text: 'Connecting...',
        };
      case 'disconnected':
        return {
          color: '#EF4444',
          bg: '#FEE2E2',
          text: 'Disconnected',
        };
      case 'error':
      default:
        return {
          color: '#EF4444',
          bg: '#FEE2E2',
          text: 'Connection Error',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }]}>
      <View style={[styles.dot, { backgroundColor: config.color }]} />
      <Text style={[styles.text, { color: config.color }]}>{config.text}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  text: {
    fontSize: 13,
    fontWeight: '600',
  },
});
