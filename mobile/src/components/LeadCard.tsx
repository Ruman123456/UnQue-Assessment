import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Lead } from '../types/lead';

interface Props {
  lead: Lead;
}

export const LeadCard: React.FC<Props> = ({ lead }) => {
  const formatTime = (timeStr?: string) => {
    if (!timeStr) return 'Just now';
    try {
      const d = new Date(timeStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + 
        ' (' + d.toLocaleDateString() + ')';
    } catch {
      return timeStr;
    }
  };

  return (
    <View style={[styles.card, lead.isNew && styles.newCard]}>
      <View style={styles.headerRow}>
        <View style={styles.nameContainer}>
          <Text style={styles.name}>{lead.name || 'Anonymous Lead'}</Text>
          {lead.isNew && (
            <View style={styles.newBadge}>
              <Text style={styles.newBadgeText}>NEW</Text>
            </View>
          )}
        </View>
        <Text style={styles.timeText}>{formatTime(lead.received_time || lead.created_time)}</Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.label}>Email:</Text>
        <Text style={styles.value} selectable>{lead.email || 'N/A'}</Text>
      </View>

      <View style={styles.detailRow}>
        <Text style={styles.label}>Phone:</Text>
        <Text style={styles.value} selectable>{lead.phone || 'N/A'}</Text>
      </View>

      <View style={styles.footerRow}>
        <Text style={styles.metaId}>Meta Lead ID: {lead.meta_lead_id}</Text>
        {lead.form_id && <Text style={styles.formId}>Form: {lead.form_id}</Text>}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  newCard: {
    borderColor: '#3B82F6',
    borderWidth: 2,
    backgroundColor: '#F8FAFC',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  nameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  name: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
  },
  newBadge: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  newBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  timeText: {
    fontSize: 12,
    color: '#64748B',
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 6,
    alignItems: 'center',
  },
  label: {
    width: 60,
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
  },
  value: {
    fontSize: 14,
    color: '#1E293B',
    flex: 1,
  },
  footerRow: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metaId: {
    fontSize: 11,
    color: '#94A3B8',
    fontFamily: 'monospace',
  },
  formId: {
    fontSize: 11,
    color: '#94A3B8',
  },
});
