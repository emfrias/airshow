// app/login.js
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../api/api';
import { setAuthToken } from '../utils/auth';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/api/login', { email, password }, {
        headers: {
          'Skip-Auth': true // Mark this request as unauthenticated
        }
      });
      const { access_token } = response.data;
      await setAuthToken(access_token);
      router.replace('/notifications');
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred during login.');
    } finally {
      setLoading(false);
    }
  };

  const navigateToSignup = () => {
    router.push('/signup');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-gray-100 justify-center items-center"
    >
      <View className="w-11/12 max-w-md p-6 bg-white rounded-xl shadow-lg">
        <Text className="text-3xl font-bold text-center text-gray-800 mb-6">Welcome Back</Text>

        {error ? (
          <Text className="text-red-500 text-center mb-4">{error}</Text>
        ) : null}

        <TextInput
          className="w-full p-4 mb-4 bg-gray-50 rounded-md border border-gray-300 text-gray-800"
          placeholder="Email"
          keyboardType="email-address"
          autoCapitalize="none"
          value={email}
          onChangeText={setEmail}
        />
        <TextInput
          className="w-full p-4 mb-6 bg-gray-50 rounded-md border border-gray-300 text-gray-800"
          placeholder="Password"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <TouchableOpacity
          className="w-full p-4 bg-blue-600 rounded-md"
          onPress={handleLogin}
          disabled={loading}
          activeOpacity={0.7}
        >
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text className="text-white text-center font-semibold text-lg">Login</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={navigateToSignup} className="mt-4">
          <Text className="text-center text-gray-600">
            Don't have an account?{' '}
            <Text className="text-blue-600 font-semibold">Sign up</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
