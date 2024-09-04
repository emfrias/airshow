// notifications.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView } from 'react-native';
import api from '../api/api'; // Import your axios instance with interceptors

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Use the interceptor logic, so no need to manually add the token
    api.get('/api/user/notifications')
      .then(response => {
        setNotifications(response.data.notifications);
      })
      .catch(error => {
        console.error('Failed to fetch notifications:', error);
      });
  }, []);

  return (
    <ScrollView className="flex-1 p-4 bg-gray-100">
      {notifications.map((notification, index) => (
        <View key={index} className="p-4 mb-4 bg-white rounded-lg shadow-md">
          <Text className="text-lg font-semibold">
            {"notification"}
          </Text>
          <Text className="text-gray-700">
            {notification.text}
          </Text>
          <Text className="text-gray-500 text-sm">
            {new Date(notification.timestamp).toLocaleString()}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

