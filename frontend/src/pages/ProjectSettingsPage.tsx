import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography, Segmented, Spin, Breadcrumb, Card, Form, Input, Button,
  Space, Table, Tag, Popconfirm, message, List, DatePicker, Modal, Select,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  AppstoreOutlined, FieldTimeOutlined, SettingOutlined,
  PlusOutlined, DeleteOutlined, UserAddOutlined,
  UpOutlined, DownOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getProject, updateProject, completeProject } from '@/api/projects';
import { createColumn, deleteColumn, reorderColumns } from '@/api/boards';
import { getLabels, createLabel, deleteLabel } from '@/api/labels';
import { useBoard } from '@/hooks/useBoard';
import {
  useProjectMembers,
  useAddProjectMember,
  useUpdateProjectMemberRole,
  useRemoveProjectMember,
} from '@/hooks/useProjects';
import { getUsers } from '@/api/admin';
import type { BoardColumn, Label, ProjectOutcome, ProjectMember, User } from '@/types';
import apiClient from '@/api/client';
import { useAuth } from '@/contexts/AuthContext';

const { Title, Text } = Typography;

const ProjectSettingsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();
  const [projectForm] = Form.useForm();
  const [labelForm] = Form.useForm();
  const [columnName, setColumnName] = useState('');
  const [outcomeOpen, setOutcomeOpen] = useState(false);
  const [outcomeForm] = Form.useForm();
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [addMemberForm] = Form.useForm();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  });

  const { data: columns } = useBoard(id);
  const { data: labels } = useQuery<Label[]>({
    queryKey: ['labels', id],
    queryFn: () => getLabels(id!),
    enabled: !!id,
  });

  const { data: outcomes } = useQuery<ProjectOutcome[]>({
    queryKey: ['outcomes', id],
    queryFn: async () => {
      const res = await apiClient.get(`/projects/${id}/outcomes`);
      return res.data;
    },
    enabled: !!id,
  });

  const { data: members } = useProjectMembers(id);
  const addMemberMutation = useAddProjectMember(id || '');
  const updateRoleMutation = useUpdateProjectMemberRole(id || '');
  const removeMemberMutation = useRemoveProjectMember(id || '');

  const { data: allUsers } = useQuery<User[]>({
    queryKey: ['admin-users'],
    queryFn: getUsers,
    enabled: currentUser?.is_superadmin || false,
  });

  // Check if current user is a manager of this project
  const isManager = currentUser?.is_superadmin ||
    members?.some((m) => m.user_id === currentUser?.id && m.role === 'manager');

  const updateProjectMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => updateProject(id!, data as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      message.success('Project updated');
    },
  });

  const completeProjectMutation = useMutation({
    mutationFn: () => completeProject(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      message.success('Project completed');
    },
  });

  const addColumnMutation = useMutation({
    mutationFn: (name: string) => createColumn(id!, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', id] });
      setColumnName('');
      message.success('Column added');
    },
  });

  const deleteColumnMutation = useMutation({
    mutationFn: (columnId: string) => deleteColumn(id!, columnId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', id] });
      message.success('Column deleted');
    },
  });

  const reorderColumnsMutation = useMutation({
    mutationFn: (columnIds: string[]) => reorderColumns(id!, columnIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', id] });
    },
  });

  const handleMoveColumn = (index: number, direction: 'up' | 'down') => {
    if (!columns) return;
    const sorted = [...columns].sort((a, b) => a.position - b.position);
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= sorted.length) return;
    const newOrder = sorted.map((c) => c.id);
    [newOrder[index], newOrder[targetIndex]] = [newOrder[targetIndex], newOrder[index]];
    reorderColumnsMutation.mutate(newOrder);
  };

  const addLabelMutation = useMutation({
    mutationFn: (data: { name: string; color: string }) => createLabel(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labels', id] });
      labelForm.resetFields();
      message.success('Label added');
    },
  });

  const deleteLabelMutation = useMutation({
    mutationFn: (labelId: string) => deleteLabel(labelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labels', id] });
      message.success('Label deleted');
    },
  });

  const addOutcomeMutation = useMutation({
    mutationFn: async (data: { title: string; description?: string; achieved_at?: string }) => {
      const res = await apiClient.post(`/projects/${id}/outcomes`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outcomes', id] });
      setOutcomeOpen(false);
      outcomeForm.resetFields();
      message.success('Outcome added');
    },
  });

  const handleViewChange = (value: string | number) => {
    if (!id) return;
    switch (value) {
      case 'Board': navigate(`/projects/${id}/board`); break;
      case 'Timeline': navigate(`/projects/${id}/timeline`); break;
      case 'Settings': navigate(`/projects/${id}/settings`); break;
    }
  };

  const handleAddMember = (values: { user_id: string; role: string }) => {
    addMemberMutation.mutate(values, {
      onSuccess: () => {
        setAddMemberOpen(false);
        addMemberForm.resetFields();
        message.success('Member added');
      },
      onError: () => message.error('Failed to add member'),
    });
  };

  if (isLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spin size="large" /></div>;
  }

  if (!project || !id) return <div>Project not found</div>;

  const memberColumns: ColumnsType<ProjectMember> = [
    {
      title: 'User',
      key: 'user',
      render: (_, record) => record.user?.display_name || record.user_id,
    },
    {
      title: 'Email',
      key: 'email',
      render: (_, record) => record.user?.email || '-',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'manager' ? 'blue' : role === 'member' ? 'green' : 'default'}>
          {role}
        </Tag>
      ),
    },
    {
      title: 'Joined',
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    ...(isManager
      ? [
          {
            title: 'Actions',
            key: 'actions',
            render: (_: unknown, record: ProjectMember) => (
              <Space>
                <Select
                  size="small"
                  value={record.role}
                  onChange={(role) =>
                    updateRoleMutation.mutate(
                      { userId: record.user_id, role },
                      {
                        onSuccess: () => message.success('Role updated'),
                        onError: () => message.error('Failed to update role'),
                      }
                    )
                  }
                  options={[
                    { value: 'manager', label: 'Manager' },
                    { value: 'member', label: 'Member' },
                    { value: 'viewer', label: 'Viewer' },
                  ]}
                  style={{ width: 100 }}
                />
                <Popconfirm
                  title="Remove member?"
                  onConfirm={() =>
                    removeMemberMutation.mutate(record.user_id, {
                      onSuccess: () => message.success('Member removed'),
                      onError: () => message.error('Failed to remove member'),
                    })
                  }
                >
                  <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          } as ColumnsType<ProjectMember>[number],
        ]
      : []),
  ];

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }} items={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: project.name },
        { title: 'Settings' },
      ]} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>{project.name} - Settings</Title>
        <Segmented
          value="Settings"
          onChange={handleViewChange}
          options={[
            { label: 'Board', value: 'Board', icon: <AppstoreOutlined /> },
            { label: 'Timeline', value: 'Timeline', icon: <FieldTimeOutlined /> },
            { label: 'Settings', value: 'Settings', icon: <SettingOutlined /> },
          ]}
        />
      </div>

      {/* Project Info */}
      <Card title="Project Info" style={{ marginBottom: 16 }}>
        <Form
          form={projectForm}
          layout="vertical"
          initialValues={{
            name: project.name,
            description: project.description,
            start_date: project.start_date ? dayjs(project.start_date) : null,
            end_date: project.end_date ? dayjs(project.end_date) : null,
          }}
          onFinish={(values) => {
            updateProjectMutation.mutate({
              ...values,
              start_date: values.start_date?.format('YYYY-MM-DD'),
              end_date: values.end_date?.format('YYYY-MM-DD'),
            });
          }}
        >
          <Form.Item name="name" label="Name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Space>
            <Form.Item name="start_date" label="Start Date">
              <DatePicker />
            </Form.Item>
            <Form.Item name="end_date" label="End Date">
              <DatePicker />
            </Form.Item>
          </Space>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">Save</Button>
              {project.status === 'active' && (
                <Popconfirm title="Complete this project?" onConfirm={() => completeProjectMutation.mutate()}>
                  <Button>Complete Project</Button>
                </Popconfirm>
              )}
            </Space>
          </Form.Item>
        </Form>
        <Text type="secondary">Prefix: {project.prefix} | Status: {project.status}</Text>
      </Card>

      {/* Members */}
      <Card
        title="Members"
        style={{ marginBottom: 16 }}
        extra={
          isManager ? (
            <Button icon={<UserAddOutlined />} onClick={() => setAddMemberOpen(true)}>
              Add Member
            </Button>
          ) : null
        }
      >
        <Table<ProjectMember>
          columns={memberColumns}
          dataSource={members || []}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>

      {/* Columns */}
      <Card title="Board Columns" style={{ marginBottom: 16 }}>
        <Table
          dataSource={columns || []}
          rowKey="id"
          pagination={false}
          size="small"
          columns={[
            { title: 'Name', dataIndex: 'name' },
            { title: 'Position', dataIndex: 'position' },
            {
              title: 'End Column',
              dataIndex: 'is_end',
              render: (v: boolean) => v ? <Tag color="green">Yes</Tag> : <Tag>No</Tag>,
            },
            { title: 'WIP Limit', dataIndex: 'wip_limit', render: (v: number | null) => v ?? '-' },
            {
              title: 'Order',
              key: 'order',
              width: 100,
              render: (_: unknown, _record: BoardColumn, index: number) => (
                <Space size={4}>
                  <Button
                    type="text"
                    size="small"
                    icon={<UpOutlined />}
                    disabled={index === 0}
                    onClick={() => handleMoveColumn(index, 'up')}
                  />
                  <Button
                    type="text"
                    size="small"
                    icon={<DownOutlined />}
                    disabled={!columns || index >= columns.length - 1}
                    onClick={() => handleMoveColumn(index, 'down')}
                  />
                </Space>
              ),
            },
            {
              title: 'Actions',
              render: (_: unknown, record: BoardColumn) =>
                !record.is_end ? (
                  <Popconfirm title="Delete column?" onConfirm={() => deleteColumnMutation.mutate(record.id)}>
                    <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                  </Popconfirm>
                ) : null,
            },
          ]}
        />
        <Space style={{ marginTop: 8 }}>
          <Input
            placeholder="New column name"
            value={columnName}
            onChange={(e) => setColumnName(e.target.value)}
            style={{ width: 200 }}
          />
          <Button icon={<PlusOutlined />} onClick={() => columnName && addColumnMutation.mutate(columnName)}>
            Add Column
          </Button>
        </Space>
      </Card>

      {/* Labels */}
      <Card title="Labels" style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          {labels?.map((label) => (
            <Tag
              key={label.id}
              color={label.color}
              closable
              onClose={() => deleteLabelMutation.mutate(label.id)}
              style={{ marginBottom: 4 }}
            >
              {label.name}
            </Tag>
          ))}
        </div>
        <Form form={labelForm} layout="inline" onFinish={(v) => addLabelMutation.mutate({ name: v.name, color: v.color })}>
          <Form.Item name="name" rules={[{ required: true }]}>
            <Input placeholder="Label name" />
          </Form.Item>
          <Form.Item name="color" initialValue="#1890ff" rules={[{ required: true }]}>
            <Input placeholder="#hex" style={{ width: 100 }} />
          </Form.Item>
          <Form.Item>
            <Button icon={<PlusOutlined />} htmlType="submit">Add</Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Outcomes */}
      <Card
        title="Project Outcomes"
        extra={<Button icon={<PlusOutlined />} onClick={() => setOutcomeOpen(true)}>Add Outcome</Button>}
      >
        <List
          dataSource={outcomes || []}
          renderItem={(outcome) => (
            <List.Item>
              <List.Item.Meta
                title={outcome.title}
                description={
                  <Space direction="vertical">
                    {outcome.description && <Text>{outcome.description}</Text>}
                    {outcome.achieved_at && <Text type="secondary">Achieved: {outcome.achieved_at}</Text>}
                  </Space>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: 'No outcomes recorded yet' }}
        />
      </Card>

      {/* Add Member Modal */}
      <Modal
        title="Add Project Member"
        open={addMemberOpen}
        onCancel={() => setAddMemberOpen(false)}
        onOk={() => addMemberForm.submit()}
        confirmLoading={addMemberMutation.isPending}
      >
        <Form form={addMemberForm} layout="vertical" onFinish={handleAddMember}>
          <Form.Item name="user_id" label="User" rules={[{ required: true }]}>
            <Select
              placeholder="Select a user"
              showSearch
              optionFilterProp="label"
              options={
                (allUsers || [])
                  .filter((u) => u.is_active && !members?.some((m) => m.user_id === u.id))
                  .map((u) => ({ value: u.id, label: `${u.display_name} (${u.username})` }))
              }
            />
          </Form.Item>
          <Form.Item name="role" label="Role" initialValue="member" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'manager', label: 'Manager' },
                { value: 'member', label: 'Member' },
                { value: 'viewer', label: 'Viewer' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Add Project Outcome"
        open={outcomeOpen}
        onCancel={() => setOutcomeOpen(false)}
        onOk={() => outcomeForm.submit()}
      >
        <Form form={outcomeForm} layout="vertical" onFinish={(v) => addOutcomeMutation.mutate({
          ...v,
          achieved_at: v.achieved_at?.format('YYYY-MM-DD'),
        })}>
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="achieved_at" label="Achieved Date">
            <DatePicker />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectSettingsPage;
