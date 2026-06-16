// src/components/ErrorBoundary.tsx
// React error boundary with fallback UI for the Pomodoro app.

import React, { Component } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  bgColor: string;
  textColor: string;
  errorColor: string;
  accentColor: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      const { bgColor, textColor, errorColor, accentColor } = this.props;

      return (
        <View style={[styles.container, { backgroundColor: bgColor }]}>
          <Text style={[styles.icon, { color: errorColor }]}>{'\u26A0'}</Text>
          <Text style={[styles.title, { color: textColor }]}>
            Something went wrong
          </Text>
          <Text style={[styles.message, { color: errorColor }]}>
            {this.state.error?.message ?? 'An unexpected error occurred.'}
          </Text>
          <TouchableOpacity
            onPress={this.handleReset}
            style={[styles.button, { backgroundColor: accentColor }]}
            accessibilityLabel="Try again"
            accessibilityRole="button"
          >
            <Text style={styles.buttonLabel}>Try Again</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  icon: {
    fontSize: 48,
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
    textAlign: 'center',
  },
  message: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  button: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  buttonLabel: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
