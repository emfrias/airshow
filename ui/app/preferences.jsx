// app/preferences/preferences.tsx

import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import api from '../api/api'; // Import your axios instance with interceptors

export default function Preferences() {
  const [topic, setTopic] = useState('');

  useEffect(() => {
    api.get('/api/user/preferences')
    .then(response => {
      setTopic(response.data.topic);
    });
  }, []);

  const savePreferences = () => {
    axios.post('/api/user/preferences', { topic }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  };

  return (
    <View className="flex-1 p-4 bg-gray-100">
      <View className="p-4 mb-4 bg-white rounded-lg shadow-md">
        <Text className="text-lg font-semibold mb-2">Preferences</Text>
        <Text className="text-gray-700 mb-2">Notification Topic</Text>
        <TextInput
          value={topic}
          onChangeText={setTopic}
          className="border p-2 rounded-lg bg-gray-50"
        />
        <TouchableOpacity
          className="w-full p-4 bg-blue-600 rounded-md"
          onPress={savePreferences}
          activeOpacity={0.7}
        >
            <Text className="text-white text-center font-semibold text-lg">Save Preferences</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

