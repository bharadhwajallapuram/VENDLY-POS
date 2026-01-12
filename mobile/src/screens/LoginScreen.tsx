/**
 * Login Screen - Authentication screen for mobile app
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { useAuthStore } from '../store/authStore';
import { Button, Input, colors, spacing, fontSize, fontWeight, radius } from '../ui';

export const LoginScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading } = useAuthStore();

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }
    
    const success = await login(email, password);
    if (!success) {
      // Get fresh error from store
      const currentError = useAuthStore.getState().error;
      Alert.alert('Login Failed', currentError || 'Unable to connect to server. Using demo mode.');
      // Fall back to demo mode
      useAuthStore.setState({ 
        isAuthenticated: true, 
        user: { id: 1, email: email, full_name: 'Demo User', role: 'admin' },
        error: null,
        isLoading: false 
      });
    }
  };
  
  // Demo login - sets authenticated without API call
  const handleDemoLogin = () => {
    // Skip API call entirely for demo
    useAuthStore.setState({ 
      isAuthenticated: true, 
      user: { id: 1, email: 'demo@vendly.com', full_name: 'Demo User', role: 'admin' },
      token: 'demo-token',
      isLoading: false 
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>V</Text>
          </View>
          <Text style={styles.appName}>Vendly POS</Text>
          <Text style={styles.tagline}>Mobile Point of Sale</Text>
        </View>

        {/* Login Form */}
        <View style={styles.form}>
          <Input
            label="Email"
            value={email}
            onChangeText={setEmail}
            placeholder="Enter your email"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!isLoading}
            icon="mail-outline"
          />

          <Input
            label="Password"
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            editable={!isLoading}
            icon="lock-closed-outline"
          />

          <Button
            title="Sign In"
            onPress={handleLogin}
            loading={isLoading}
            fullWidth
            size="lg"
            style={styles.loginButton}
          />

          <Button
            title="Demo Login (Skip)"
            onPress={handleDemoLogin}
            variant="outline"
            fullWidth
          />
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Version 1.0.0</Text>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.xxl,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing.xxxl + spacing.lg,
  },
  logo: {
    width: 80,
    height: 80,
    borderRadius: radius.xxl,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  logoText: {
    fontSize: 40,
    fontWeight: fontWeight.bold,
    color: colors.white,
  },
  appName: {
    fontSize: fontSize.xxxl,
    fontWeight: fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontSize: fontSize.lg,
    color: colors.textSecondary,
  },
  form: {
    gap: spacing.lg,
  },
  loginButton: {
    marginTop: spacing.sm,
  },
  footer: {
    alignItems: 'center',
    marginTop: spacing.xxxl + spacing.lg,
  },
  footerText: {
    fontSize: fontSize.sm,
    color: colors.textMuted,
  },
});

export default LoginScreen;
