import React, { useEffect, useState } from 'react';
import { View, Text, Platform } from 'react-native';
import { WebView } from 'react-native-webview';
import api from '../../api/api';
import { useRouter } from 'expo-router';

// Web-specific imports (conditionally loaded)
let MapContainer, TileLayer, Marker, Popup, Polyline, L;
if (Platform.OS === 'web') {
  MapContainer = require('react-leaflet').MapContainer;
  TileLayer = require('react-leaflet').TileLayer;
  Marker = require('react-leaflet').Marker;
  Popup = require('react-leaflet').Popup;
  Polyline = require('react-leaflet').Polyline;
  L = require('leaflet');
  require('leaflet/dist/leaflet.css');
}

// Shared logic to create markers and polylines
const createMapElements = (location, aircraft) => {
  const markers = [
    {
      position: [location.latitude, location.longitude],
      popupText: 'You are here',
      icon: null, // Default marker
    },
    {
      position: [aircraft.latitude, aircraft.longitude],
      popupText: 'Aircraft here',
      icon: L && L.icon({
        iconUrl: 'https://example.com/airplane.png',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      }), // Use airplane sprite for web
    },
  ];

  const polyline = [
    [location.latitude, location.longitude],
    [aircraft.latitude, aircraft.longitude],
    [aircraft.latitude + 0.02, aircraft.longitude + 0.02], // Simulated future position
  ];

  return { markers, polyline };
};

// Mobile map view using WebView and Leaflet HTML
const MobileMapView = ({ location, aircraft }) => {
  const mapHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
          #map { height: 100vh; width: 100vw; }
        </style>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
      </head>
      <body>
        <div id="map"></div>
        <script>
          var map = L.map('map').setView([${location.latitude}, ${location.longitude}], 13);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          }).addTo(map);

          L.marker([${location.latitude}, ${location.longitude}]).addTo(map)
            .bindPopup('You are here').openPopup();

          L.marker([${aircraft.latitude}, ${aircraft.longitude}], {
            icon: L.icon({
              iconUrl: 'https://example.com/airplane.png',
              iconSize: [32, 32],
              iconAnchor: [16, 16]
            })
          }).addTo(map).bindPopup('Aircraft here');

          L.polyline([
            [${location.latitude}, ${location.longitude}],
            [${aircraft.latitude}, ${aircraft.longitude}],
            [${aircraft.latitude + 0.02}, ${aircraft.longitude + 0.02}]
          ], { color: 'blue' }).addTo(map);
        </script>
      </body>
    </html>
  `;

  return (
    <WebView
      originWhitelist={['*']}
      source={{ html: mapHtml }}
      style={{ flex: 1 }}
      javaScriptEnabled={true}
    />
  );
};

// Web map view using react-leaflet
const WebMapView = ({ location, aircraft }) => {
  const { markers, polyline } = createMapElements(location, aircraft);

  return (
    <MapContainer
      center={[location.latitude, location.longitude]}
      zoom={13}
      style={{ height: '100vh', width: '100vw' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="Map data © OpenStreetMap contributors"
      />
      {markers.map((marker, index) => (
        <Marker key={index} position={marker.position} icon={marker.icon}>
          <Popup>{marker.popupText}</Popup>
        </Marker>
      ))}
      <Polyline positions={polyline} color="blue" />
    </MapContainer>
  );
};

// Main LocationScreen component
export default function LocationScreen() {
  const [location, setLocation] = useState(null);
  const [aircraft, setAircraft] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const fetchLocation = async () => {
      try {
        const response = await api.get('/api/user/location');
        setLocation(response.data);

        // Simulate aircraft data for the example
        const aircraftData = {
          latitude: response.data.latitude + 0.01,
          longitude: response.data.longitude + 0.01,
        };
        setAircraft(aircraftData);
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

  if (!location || !aircraft) {
    return <View><Text>Loading map...</Text></View>;
  }

  return (
    <View style={{ flex: 1 }}>
      {Platform.OS === 'web' ? (
        <WebMapView location={location} aircraft={aircraft} />
      ) : (
        <MobileMapView location={location} aircraft={aircraft} />
      )}
    </View>
  );
}

