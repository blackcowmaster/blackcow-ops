// src/components/TaskInput.tsx
// Text input + add button for creating new tasks.

import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
} from 'react-native';

interface TaskInputProps {
  onSubmit: (title: string) => void;
  placeholder?: string;
  bgColor: string;
  textColor: string;
  secondaryColor: string;
  accentColor: string;
  borderColor: string;
}

export function TaskInput({
  onSubmit,
  placeholder = 'Add a task...',
  bgColor,
  textColor,
  secondaryColor,
  accentColor,
  borderColor,
}: TaskInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed.length === 0) return;
    onSubmit(trimmed);
    setValue('');
  };

  return (
    <View style={[styles.container, { borderColor, backgroundColor: bgColor }]}>
      <TextInput
        style={[
          styles.input,
          { color: textColor },
        ]}
        value={value}
        onChangeText={setValue}
        placeholder={placeholder}
        placeholderTextColor={secondaryColor}
        onSubmitEditing={handleSubmit}
        returnKeyType="done"
        maxLength={200}
        autoCorrect={false}
        accessibilityLabel="Task title input"
      />
      <TouchableOpacity
        onPress={handleSubmit}
        disabled={value.trim().length === 0}
        style={[
          styles.addButton,
          {
            backgroundColor:
              value.trim().length > 0 ? accentColor : borderColor,
          },
        ]}
        accessibilityLabel="Add task"
        accessibilityRole="button"
      >
        <Text style={styles.addLabel}>Add</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    paddingLeft: 16,
    paddingRight: 8,
    paddingVertical: 4,
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
  },
  addButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
  },
  addLabel: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
});
