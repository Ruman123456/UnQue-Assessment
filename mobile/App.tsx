import React from 'react';
import { StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LeadsScreen } from './src/screens/LeadsScreen';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <LeadsScreen />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F1F5F9',
  },
});
