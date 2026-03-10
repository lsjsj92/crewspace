import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Space } from 'antd';
import { MailOutlined, LockOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { register as apiRegister } from '@/api/auth';
import type { RegisterRequest } from '@/types';

const { Title, Text, Link } = Typography;

const LoginPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.email, values.password);
      message.success('Login successful!');
      navigate('/dashboard', { replace: true });
    } catch {
      message.error('Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: RegisterRequest) => {
    setLoading(true);
    try {
      await apiRegister(values);
      message.success('Registration successful! Please log in.');
      setIsRegister(false);
      form.resetFields();
    } catch {
      message.error('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 4 }}>
            Planship
          </Title>
          <Text type="secondary">{isRegister ? 'Create your account' : 'Sign in to your account'}</Text>
        </div>

        {isRegister ? (
          <Form form={form} layout="vertical" onFinish={handleRegister} autoComplete="off">
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
            </Form.Item>
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Please enter a username' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="Username" size="large" />
            </Form.Item>
            <Form.Item
              name="display_name"
              rules={[{ required: true, message: 'Please enter your display name' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="Display Name" size="large" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please enter a password' },
                { min: 6, message: 'Password must be at least 6 characters' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block size="large">
                Register
              </Button>
            </Form.Item>
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Text>Already have an account?</Text>
              <Link onClick={() => setIsRegister(false)}>Sign in</Link>
            </Space>
          </Form>
        ) : (
          <Form form={form} layout="vertical" onFinish={handleLogin} autoComplete="off">
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please enter your email' },
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please enter your password' }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block size="large">
                Sign In
              </Button>
            </Form.Item>
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Text>Don't have an account?</Text>
              <Link onClick={() => setIsRegister(true)}>Register</Link>
            </Space>
          </Form>
        )}
      </Card>
    </div>
  );
};

export default LoginPage;
