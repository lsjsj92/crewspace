// frontend/src/pages/ProfilePage.tsx
import React from 'react';
import {
  Typography, Card, Form, Input, Button, Descriptions, message,
} from 'antd';
import { useAuth } from '@/contexts/AuthContext';
import { updateMyProfile, changeMyPassword } from '@/api/profile';

const { Title } = Typography;

const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  if (!user) return null;

  const handleProfileUpdate = async (values: { display_name: string; organization?: string }) => {
    try {
      await updateMyProfile(values);
      await refreshUser();
      message.success('Profile updated');
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Failed to update profile';
      message.error(detail);
    }
  };

  const handlePasswordChange = async (values: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('New passwords do not match');
      return;
    }
    try {
      await changeMyPassword({
        current_password: values.current_password,
        new_password: values.new_password,
      });
      passwordForm.resetFields();
      message.success('Password changed');
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Failed to change password';
      message.error(detail);
    }
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>My Profile</Title>

      <Card title="Account Information" style={{ marginBottom: 16 }}>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Email">{user.email}</Descriptions.Item>
          <Descriptions.Item label="Username">{user.username}</Descriptions.Item>
          {user.employee_id && (
            <Descriptions.Item label="Employee ID">{user.employee_id}</Descriptions.Item>
          )}
          {user.gw_id && (
            <Descriptions.Item label="GW ID">{user.gw_id}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card title="Edit Profile" style={{ marginBottom: 16 }}>
        <Form
          form={profileForm}
          layout="vertical"
          initialValues={{
            display_name: user.display_name,
            organization: user.organization || '',
          }}
          onFinish={handleProfileUpdate}
        >
          <Form.Item
            name="display_name"
            label="Display Name"
            rules={[{ required: true, message: 'Display name is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="organization" label="Organization">
            <Input />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">Save</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Change Password">
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            name="current_password"
            label="Current Password"
            rules={[{ required: true, message: 'Current password is required' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="New Password"
            rules={[
              { required: true, message: 'New password is required' },
              { min: 4, message: 'Password must be at least 4 characters' },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="Confirm New Password"
            rules={[
              { required: true, message: 'Please confirm your new password' },
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">Change Password</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ProfilePage;
