import React, { useEffect, useState } from 'react';
import {
  Table, Tag, Space, Typography, message, Tabs, Switch, Button,
  Modal, Form, Input, Select, Popconfirm,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { PlusOutlined, UploadOutlined, DeleteOutlined, LockOutlined, EditOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import {
  getUsers, updateUser, deactivateUser, createUser, importHR,
  deleteTeam, resetUserPassword, adminUpdateUser,
} from '@/api/admin';
import { getMyTeams } from '@/api/teams';
import { getProjects, createProject, deleteProject } from '@/api/projects';
import type { User, Team, Project } from '@/types';

const { Title, Text } = Typography;

const AdminPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  const invalidateRelatedQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['teams'] });
    queryClient.invalidateQueries({ queryKey: ['board'] });
    queryClient.invalidateQueries({ queryKey: ['project-members'] });
  };

  const [users, setUsers] = useState<User[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingTeams, setLoadingTeams] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const [resetPasswordUserId, setResetPasswordUserId] = useState<string | null>(null);
  const [editUserOpen, setEditUserOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deleteProjectOpen, setDeleteProjectOpen] = useState(false);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [deleteProjectConfirm, setDeleteProjectConfirm] = useState('');
  const [userForm] = Form.useForm();
  const [editUserForm] = Form.useForm();
  const [projectForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const data = await getUsers();
      setUsers(data);
    } catch {
      message.error('Failed to load users');
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchTeams = async () => {
    setLoadingTeams(true);
    try {
      const data = await getMyTeams();
      setTeams(data);
    } catch {
      message.error('Failed to load teams');
    } finally {
      setLoadingTeams(false);
    }
  };

  const fetchProjects = async () => {
    setLoadingProjects(true);
    try {
      const data = await getProjects();
      setProjects(data);
    } catch {
      message.error('Failed to load projects');
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    if (currentUser?.is_superadmin) {
      fetchUsers();
      fetchTeams();
      fetchProjects();
    }
  }, [currentUser]);

  if (!currentUser?.is_superadmin) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Title level={3}>Access Denied</Title>
        <Text type="secondary">This page is only accessible to system administrators.</Text>
      </div>
    );
  }

  const handleToggleActive = async (record: User) => {
    try {
      if (record.is_active) {
        await deactivateUser(record.id);
        message.success(`${record.display_name} has been deactivated`);
      } else {
        await updateUser(record.id, { is_active: true });
        message.success(`${record.display_name} has been activated`);
      }
      fetchUsers();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to update user status');
    }
  };

  const handleHRImport = async () => {
    try {
      const result = await importHR();
      message.success(
        `HR Import: ${result.imported_count} imported, ${result.updated_count} updated, ${result.skipped_count} skipped, ${result.team_created_count} teams created`
      );
      fetchUsers();
      fetchTeams();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to import HR data');
    }
  };

  const handleCreateUser = async (values: {
    email: string; username: string; display_name: string; password: string;
    employee_id?: string; organization?: string; gw_id?: string;
  }) => {
    try {
      await createUser(values);
      message.success('User created');
      setCreateUserOpen(false);
      userForm.resetFields();
      fetchUsers();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to create user');
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    try {
      await deleteTeam(teamId);
      message.success('Team deleted');
      fetchTeams();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to delete team');
    }
  };

  const openDeleteProjectModal = (project: Project) => {
    setDeletingProject(project);
    setDeleteProjectConfirm('');
    setDeleteProjectOpen(true);
  };

  const handleDeleteProject = async () => {
    if (!deletingProject || deleteProjectConfirm !== deletingProject.name) return;
    try {
      await deleteProject(deletingProject.id);
      message.success('Project deleted');
      setDeleteProjectOpen(false);
      setDeletingProject(null);
      setDeleteProjectConfirm('');
      fetchProjects();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to delete project');
    }
  };

  const handleCreateProject = async (values: Record<string, string>) => {
    try {
      await createProject({
        name: values.name,
        description: values.description,
        prefix: values.prefix,
        start_date: values.start_date,
        end_date: values.end_date,
        manager_user_id: values.manager_user_id,
      });
      message.success('Project created');
      setCreateProjectOpen(false);
      projectForm.resetFields();
      fetchProjects();
      invalidateRelatedQueries();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || 'Failed to create project';
      message.error(detail);
    }
  };

  const handleResetPassword = async (values: { new_password: string }) => {
    if (!resetPasswordUserId) return;
    try {
      await resetUserPassword(resetPasswordUserId, values.new_password);
      message.success('Password updated');
      setResetPasswordOpen(false);
      setResetPasswordUserId(null);
      passwordForm.resetFields();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to reset password');
    }
  };

  const openEditUserModal = (record: User) => {
    setEditingUser(record);
    editUserForm.setFieldsValue({
      email: record.email,
      username: record.username,
      display_name: record.display_name,
      is_active: record.is_active,
      is_superadmin: record.is_superadmin,
      employee_id: record.employee_id || '',
      organization: record.organization || '',
      gw_id: record.gw_id || '',
    });
    setEditUserOpen(true);
  };

  const handleEditUser = async (values: Record<string, unknown>) => {
    if (!editingUser) return;
    try {
      const data: Record<string, unknown> = {};
      if (values.email !== editingUser.email) data.email = values.email;
      if (values.username !== editingUser.username) data.username = values.username;
      if (values.display_name !== editingUser.display_name) data.display_name = values.display_name;
      if (values.is_active !== editingUser.is_active) data.is_active = values.is_active;
      if (values.is_superadmin !== editingUser.is_superadmin) data.is_superadmin = values.is_superadmin;
      data.employee_id = (values.employee_id as string) || null;
      data.organization = (values.organization as string) || null;
      data.gw_id = (values.gw_id as string) || null;

      await adminUpdateUser(editingUser.id, data as Parameters<typeof adminUpdateUser>[1]);
      message.success('User updated');
      setEditUserOpen(false);
      setEditingUser(null);
      editUserForm.resetFields();
      fetchUsers();
      invalidateRelatedQueries();
    } catch {
      message.error('Failed to update user');
    }
  };

  const openResetPasswordModal = (userId: string) => {
    setResetPasswordUserId(userId);
    setResetPasswordOpen(true);
    passwordForm.resetFields();
  };

  const userColumns: ColumnsType<User> = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
    },
    {
      title: 'Display Name',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Employee ID',
      dataIndex: 'employee_id',
      key: 'employee_id',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Organization',
      dataIndex: 'organization',
      key: 'organization',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'GW ID',
      dataIndex: 'gw_id',
      key: 'gw_id',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) =>
        isActive ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>,
      filters: [
        { text: 'Active', value: true },
        { text: 'Inactive', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: 'Role',
      dataIndex: 'is_superadmin',
      key: 'is_superadmin',
      render: (isSuperadmin: boolean) =>
        isSuperadmin ? <Tag color="purple">Superadmin</Tag> : <Tag>User</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditUserModal(record)}
          >
            Edit
          </Button>
          <Switch
            checked={record.is_active}
            onChange={() => handleToggleActive(record)}
            checkedChildren="Active"
            unCheckedChildren="Inactive"
            disabled={record.id === currentUser?.id}
          />
          <Button
            type="text"
            size="small"
            icon={<LockOutlined />}
            onClick={() => openResetPasswordModal(record.id)}
            disabled={record.id === currentUser?.id}
          >
            Reset PW
          </Button>
        </Space>
      ),
    },
  ];

  const teamColumns: ColumnsType<Team> = [
    {
      title: 'Team Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Members',
      dataIndex: 'member_count',
      key: 'member_count',
      sorter: (a, b) => (a.member_count || 0) - (b.member_count || 0),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) =>
        isActive ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Popconfirm
          title="Delete this team?"
          description="This action cannot be undone."
          onConfirm={() => handleDeleteTeam(record.id)}
        >
          <Button type="text" danger size="small" icon={<DeleteOutlined />}>
            Delete
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const projectColumns: ColumnsType<Project> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'Prefix',
      dataIndex: 'prefix',
      key: 'prefix',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : status === 'completed' ? 'blue' : 'default'}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => openDeleteProjectModal(record)}
        >
          Delete
        </Button>
      ),
    },
  ];

  const tabItems = [
    {
      key: 'users',
      label: `Users (${users.length})`,
      children: (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateUserOpen(true)}>
              Add User
            </Button>
            <Button icon={<UploadOutlined />} onClick={handleHRImport}>
              HR Import
            </Button>
          </Space>
          <Table<User>
            columns={userColumns}
            dataSource={users}
            rowKey="id"
            loading={loadingUsers}
            pagination={{ pageSize: 20, showSizeChanger: true }}
          />
        </div>
      ),
    },
    {
      key: 'teams',
      label: `Teams (${teams.length})`,
      children: (
        <Table<Team>
          columns={teamColumns}
          dataSource={teams}
          rowKey="id"
          loading={loadingTeams}
          pagination={{ pageSize: 20, showSizeChanger: true }}
        />
      ),
    },
    {
      key: 'projects',
      label: `Projects (${projects.length})`,
      children: (
        <div>
          <Space style={{ marginBottom: 16 }}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateProjectOpen(true)}>
              Create Project
            </Button>
          </Space>
          <Table<Project>
            columns={projectColumns}
            dataSource={projects}
            rowKey="id"
            loading={loadingProjects}
            pagination={{ pageSize: 20, showSizeChanger: true }}
          />
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>System Administration</Title>
      <Tabs items={tabItems} />

      {/* Create User Modal */}
      <Modal
        title="Create User"
        open={createUserOpen}
        onCancel={() => setCreateUserOpen(false)}
        onOk={() => userForm.submit()}
      >
        <Form form={userForm} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="display_name" label="Display Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 4 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="employee_id" label="Employee ID">
            <Input />
          </Form.Item>
          <Form.Item name="organization" label="Organization">
            <Input />
          </Form.Item>
          <Form.Item name="gw_id" label="GW ID">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Project Modal */}
      <Modal
        title="Create Project"
        open={createProjectOpen}
        onCancel={() => setCreateProjectOpen(false)}
        onOk={() => projectForm.submit()}
      >
        <Form form={projectForm} layout="vertical" onFinish={handleCreateProject}>
          <Form.Item name="name" label="Project Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="prefix" label="Prefix" rules={[{ required: true, max: 10 }]}>
            <Input placeholder="e.g., PROJ" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="manager_user_id" label="Manager">
            <Select
              placeholder="Select a manager"
              allowClear
              showSearch
              optionFilterProp="label"
              options={users
                .filter((u) => u.is_active)
                .map((u) => ({ value: u.id, label: `${u.display_name} (${u.username})` }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        title="Edit User"
        open={editUserOpen}
        onCancel={() => {
          setEditUserOpen(false);
          setEditingUser(null);
          editUserForm.resetFields();
        }}
        onOk={() => editUserForm.submit()}
        width={520}
      >
        <Form form={editUserForm} layout="vertical" onFinish={handleEditUser}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="display_name" label="Display Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Space size={16}>
            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch disabled={editingUser?.id === currentUser?.id} />
            </Form.Item>
            <Form.Item name="is_superadmin" label="Superadmin" valuePropName="checked">
              <Switch disabled={editingUser?.id === currentUser?.id} />
            </Form.Item>
          </Space>
          <Form.Item name="employee_id" label="Employee ID">
            <Input />
          </Form.Item>
          <Form.Item name="organization" label="Organization">
            <Input />
          </Form.Item>
          <Form.Item name="gw_id" label="GW ID">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* Delete Project Modal */}
      <Modal
        title="Delete Project"
        open={deleteProjectOpen}
        onCancel={() => {
          setDeleteProjectOpen(false);
          setDeletingProject(null);
          setDeleteProjectConfirm('');
        }}
        onOk={handleDeleteProject}
        okButtonProps={{
          danger: true,
          disabled: deleteProjectConfirm !== deletingProject?.name,
        }}
        okText="Delete"
      >
        <p>
          This action cannot be undone. To confirm, type the project name:{' '}
          <Text strong>{deletingProject?.name}</Text>
        </p>
        <Input
          placeholder="Type project name to confirm"
          value={deleteProjectConfirm}
          onChange={(e) => setDeleteProjectConfirm(e.target.value)}
        />
      </Modal>

      {/* Reset Password Modal */}
      <Modal
        title="Reset Password"
        open={resetPasswordOpen}
        onCancel={() => {
          setResetPasswordOpen(false);
          setResetPasswordUserId(null);
          passwordForm.resetFields();
        }}
        onOk={() => passwordForm.submit()}
      >
        <Form form={passwordForm} layout="vertical" onFinish={handleResetPassword}>
          <Form.Item
            name="new_password"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter a new password' },
              { min: 4, message: 'Password must be at least 4 characters' },
            ]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminPage;
