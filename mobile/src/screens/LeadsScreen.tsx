import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { Lead, ConnectionStatus, WebSocketMessage } from '../types/lead';
import { fetchExistingLeads, WebSocketClient, getBackendUrls } from '../services/api';
import { LeadCard } from '../components/LeadCard';
import { ConnectionBadge } from '../components/ConnectionBadge';

export const LeadsScreen: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const wsClientRef = useRef<WebSocketClient | null>(null);

  useEffect(() => {
    // 1. Initial REST call to load existing leads
    const loadInitialLeads = async () => {
      try {
        setLoading(true);
        const existingLeads = await fetchExistingLeads();
        setLeads(existingLeads);
      } catch (err) {
        console.warn('Failed to load initial leads:', err);
      } finally {
        setLoading(false);
      }
    };

    loadInitialLeads();

    // 2. Establish WebSocket connection
    const { wsUrl } = getBackendUrls();
    const client = new WebSocketClient(
      wsUrl,
      (message: WebSocketMessage) => {
        handleIncomingMessage(message);
      },
      (newStatus: ConnectionStatus) => {
        setStatus(newStatus);
      }
    );

    wsClientRef.current = client;
    client.connect();

    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
      }
    };
  }, []);

  const handleIncomingMessage = (message: WebSocketMessage) => {
    if (message.type === 'new_lead' && message.lead) {
      const incomingLead = { ...message.lead, isNew: true };

      setLeads((prevLeads) => {
        // Prevent duplicate lead insertion
        const exists = prevLeads.some(
          (l) => l.meta_lead_id === incomingLead.meta_lead_id || l.id === incomingLead.id
        );
        if (exists) {
          return prevLeads;
        }
        // Prepend new lead directly to the top so it's immediately visible
        return [incomingLead, ...prevLeads];
      });
    } else if (message.type === 'leads_cleared') {
      setLeads([]);
    }
  };

  const renderEmptyState = () => {
    if (loading) {
      return (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.emptySubtitle}>Loading leads from backend...</Text>
        </View>
      );
    }
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyTitle}>No Leads Received Yet</Text>
        <Text style={styles.emptySubtitle}>
          Submit a test lead via Meta Lead Testing Tool to see it arrive automatically in real time.
        </Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F8FAFC" />

      {/* Top App Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>LEADS</Text>
          <Text style={styles.headerSubtitle}>Meta Lead Ads Live Sync</Text>
        </View>
        <ConnectionBadge status={status} />
      </View>

      {/* Stats Bar */}
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Total Leads</Text>
          <Text style={styles.statValue}>{leads.length}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Sync Mode</Text>
          <Text style={styles.statValueHighlight}>WebSocket Live</Text>
        </View>
      </View>

      {/* Leads List */}
      <FlatList
        data={leads}
        keyExtractor={(item) => item.meta_lead_id || item.id.toString()}
        renderItem={({ item }) => <LeadCard lead={item} />}
        contentContainerStyle={leads.length === 0 ? styles.emptyListContent : styles.listContent}
        ListEmptyComponent={renderEmptyState}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F1F5F9',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 14,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: 0.5,
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  statValueHighlight: {
    fontSize: 14,
    fontWeight: '700',
    color: '#10B981',
  },
  listContent: {
    paddingVertical: 8,
  },
  emptyListContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  centerContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 4,
  },
});
