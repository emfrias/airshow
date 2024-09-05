import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import MapView, { Marker } from '../../components/mymap';
//import MapView, { Marker } from 'react-native-maps';
import api from '../../api/api';
import { useRouter } from 'expo-router';

export default function LocationScreen() {
  const [location, setLocation] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const fetchLocation = async () => {
      try {
        const response = await api.get('/api/user/location');
        setLocation(response.data);
      } catch (error) {
        if (error.response && error.response.status === 401) {
          router.replace('/login');
        } else {
          console.error('Failed to fetch location:', error);
        }
      }
    };

    fetchLocation();
  }, []);

  const renderTimeAgo = (reportedAt) => {
    const diff = Math.floor((new Date() - new Date(reportedAt)) / 60000);
    if (diff < 1) return 'Just now';
    if (diff === 1) return '1 minute ago';
    return `${diff} minutes ago`;
  };

  if (!location) {
    return <Text>Loading location...</Text>;
  }

  return (
    <View className="flex-1">
      <MapView
        style={{ flex: 1 }}
        initialRegion={{
          latitude: location.latitude,
          longitude: location.longitude,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }}
      >
        <Marker coordinate={{ latitude: location.latitude, longitude: location.longitude }} />
      </MapView>
      <View className="p-4 bg-white">
        <Text className="text-center text-lg">Last updated: {renderTimeAgo(location.reported_at)}</Text>
      </View>
    </View>
  );
}
