import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  Card,
  Title,
  TextInput,
  Button,
  Text,
  ActivityIndicator,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import APIService from '../services/APIService';
import { colors, spacing } from '../theme/colors';

interface RegisterScreenProps {
  navigation: any;
  onRegistrationSuccess: (userData: any) => void;
}

const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation, onRegistrationSuccess }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleRegister = async () => {
    // Validation
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password.trim()) {
      Alert.alert('Validation Error', 'Please fill in all fields');
      return;
    }

    if (!isValidEmail(email)) {
      Alert.alert('Validation Error', 'Please enter a valid email address');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Validation Error', 'Password must be at least 6 characters long');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Validation Error', 'Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const response = await APIService.register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim().toLowerCase(),
        password: password,
      });
      
      // Success - user is now registered and logged in
      Alert.alert('Success', 'Account created successfully!', [
        {
          text: 'OK',
          onPress: () => {
            onRegistrationSuccess(response.user);
            navigation.goBack();
          }
        }
      ]);
    } catch (error: any) {
      console.error('Registration error:', error);
      
      let errorMessage = 'Registration failed. Please try again.';
      if (error.response?.status === 400) {
        errorMessage = 'Email already registered. Please use a different email or sign in.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      Alert.alert('Registration Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const navigateToLogin = () => {
    navigation.goBack();
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Icon name="account-plus" size={64} color={colors.primary} />
          <Title style={styles.title}>Create Account</Title>
          <Text style={styles.subtitle}>Join us to discover amazing restaurant deals</Text>
        </View>

        <Card style={styles.registerCard}>
          <Card.Content>
            <View style={styles.form}>
              <View style={styles.nameRow}>
                <TextInput
                  label="First Name"
                  value={firstName}
                  onChangeText={setFirstName}
                  mode="outlined"
                  autoCapitalize="words"
                  autoComplete="given-name"
                  style={[styles.input, styles.nameInput]}
                  left={<TextInput.Icon icon="account" />}
                  disabled={loading}
                />
                <TextInput
                  label="Last Name"
                  value={lastName}
                  onChangeText={setLastName}
                  mode="outlined"
                  autoCapitalize="words"
                  autoComplete="family-name"
                  style={[styles.input, styles.nameInput]}
                  disabled={loading}
                />
              </View>

              <TextInput
                label="Email"
                value={email}
                onChangeText={setEmail}
                mode="outlined"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                autoComplete="email"
                style={styles.input}
                left={<TextInput.Icon icon="email" />}
                disabled={loading}
              />

              <TextInput
                label="Password"
                value={password}
                onChangeText={setPassword}
                mode="outlined"
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoComplete="password-new"
                style={styles.input}
                left={<TextInput.Icon icon="lock" />}
                right={
                  <TextInput.Icon 
                    icon={showPassword ? "eye-off" : "eye"}
                    onPress={() => setShowPassword(!showPassword)}
                  />
                }
                disabled={loading}
              />

              <TextInput
                label="Confirm Password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                mode="outlined"
                secureTextEntry={!showConfirmPassword}
                autoCapitalize="none"
                autoComplete="password-new"
                style={styles.input}
                left={<TextInput.Icon icon="lock-check" />}
                right={
                  <TextInput.Icon 
                    icon={showConfirmPassword ? "eye-off" : "eye"}
                    onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                  />
                }
                disabled={loading}
              />

              <Button 
                mode="contained" 
                onPress={handleRegister}
                disabled={loading}
                style={styles.registerButton}
                contentStyle={styles.buttonContent}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  'Create Account'
                )}
              </Button>

              <View style={styles.divider}>
                <Text style={styles.dividerText}>Already have an account?</Text>
              </View>

              <Button 
                mode="outlined" 
                onPress={navigateToLogin}
                disabled={loading}
                style={styles.loginButton}
                contentStyle={styles.buttonContent}
              >
                Sign In
              </Button>
            </View>
          </Card.Content>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.md,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  registerCard: {
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  form: {
    paddingVertical: spacing.md,
  },
  nameRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  input: {
    marginBottom: spacing.md,
  },
  nameInput: {
    flex: 1,
  },
  registerButton: {
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  buttonContent: {
    paddingVertical: spacing.sm,
  },
  divider: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  dividerText: {
    color: colors.textLight,
    fontSize: 14,
  },
  loginButton: {
    borderColor: colors.primary,
  },
});

export default RegisterScreen;