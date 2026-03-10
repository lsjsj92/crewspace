import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Card,
  Table,
  Tag,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Spin,
  Popconfirm,
  message,
  List,
} from 'antd';
import {
  PlusOutlined,
  ProjectOutlined,
  UserAddOutlined,
  DeleteOutlined,
  CrownOutlined,
} from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTeam, useTeamProjects } from '@/hooks/useTeams';
import { useAuth } from '@/contexts/AuthContext';
import { addTeamMember, removeTeamMember, updateMemberRole } from '@/api/teams';
import { createProject } from '@/api/projects';
import type { TeamMember } from '@/types';

const { Title, Text, Paragraph } = Typography;

const ROLE_COLORS: Record<string, string> = {
  owner: 'gold',
  manager: 'blue',
  member: 'green',
  viewer: 'default',
};

const ROLE_OPTIONS = [
  { value: 'manager', label: 'Manager' },
  { value: 'member', label: 'Member' },
  { value: 'viewer', label: 'Viewer' },
];

const TeamPage: React.FC = () => {
  const { teamId: teamIdParam } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const teamId = teamIdParam;

  const { data: team, isLoading: teamLoading } = useTeam(teamId);
  const { data: projects, isLoading: projectsLoading } = useTeamProjects(teamId);

  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [addMemberForm] = Form.useForm();
  const [createProjectForm] = Form.useForm();

  const currentMember = team?.members?.find((m) => m.user_id === user?.id);
  const isManagerOrOwner = currentMember?.role === 'owner' || currentMember?.role === 'manager';

  const addMemberMutation = useMutation({
    mutationFn: (data: { email: string; role: string }) => addTeamMember(teamId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
      setAddMemberOpen(false);
      addMemberForm.resetFields();
      message.success('Member added');
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || 'Failed to add member';
      message.error(detail);
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => removeTeamMember(teamId!, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
      message.success('Member removed');
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateMemberRole(teamId!, userId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] });
      message.success('Role updated');
    },
  });

  const createProjectMutation = useMutation({
    mutationFn: (data: { name: string; description?: string; prefix: string }) =>
      createProject(data),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId, 'projects'] });
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setCreateProjectOpen(false);
      createProjectForm.resetFields();
      message.success('Project created');
      navigate(`/projects/${project.id}/board`);
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || 'Failed to create project';
      message.error(detail);
    },
  });

  const memberColumns = [
    {
      title: 'User',
      key: 'user',
      render: (_: unknown, record: TeamMember) => (
        <Space>
          {record.role === 'owner' && <CrownOutlined style={{ color: '#faad14' }} />}
          <Text>{record.user?.display_name || record.user?.username || `User ${record.user_id}`}</Text>
        </Space>
      ),
    },
    {
      title: 'Email',
      key: 'email',
      render: (_: unknown, record: TeamMember) => record.user?.email || '-',
    },
    {
      title: 'Role',
      key: 'role',
      render: (_: unknown, record: TeamMember) => {
        if (record.role === 'owner' || !isManagerOrOwner) {
          return <Tag color={ROLE_COLORS[record.role]}>{record.role.toUpperCase()}</Tag>;
        }
        return (
          <Select
            value={record.role}
            size="small"
            style={{ width: 100 }}
            onChange={(role) => updateRoleMutation.mutate({ userId: record.user_id, role })}
            options={ROLE_OPTIONS}
          />
        );
      },
    },
    ...(isManagerOrOwner
      ? [
          {
            title: 'Actions',
            key: 'actions',
            render: (_: unknown, record: TeamMember) => {
              if (record.role === 'owner') return null;
              return (
                <Popconfirm
                  title="Remove this member?"
                  onConfirm={() => removeMemberMutation.mutate(record.user_id)}
                >
                  <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                </Popconfirm>
              );
            },
          },
        ]
      : []),
  ];

  if (teamLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!team || !teamId) {
    return <div>Team not found</div>;
  }

  return (
    <div>
      <Title level={3}>{team.name}</Title>
      {team.description && (
        <Paragraph type="secondary">{team.description}</Paragraph>
      )}

      {/* Members Section */}
      <Card
        title="Members"
        extra={
          isManagerOrOwner && (
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={() => setAddMemberOpen(true)}
            >
              Add Member
            </Button>
          )
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          dataSource={team.members || []}
          columns={memberColumns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>

      {/* Projects Section */}
      <Card
        title="Projects"
        extra={
          isManagerOrOwner && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateProjectOpen(true)}
            >
              Create Project
            </Button>
          )
        }
      >
        {projectsLoading ? (
          <Spin />
        ) : (
          <List
            dataSource={projects || []}
            renderItem={(project) => (
              <List.Item
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/projects/${project.id}/board`)}
                actions={[
                  <Tag key="status" color={project.status === 'active' ? 'green' : 'default'}>
                    {project.status}
                  </Tag>,
                ]}
              >
                <List.Item.Meta
                  avatar={<ProjectOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                  title={project.name}
                  description={
                    <Space>
                      <Text type="secondary">Prefix: {project.prefix}</Text>
                      {project.description && (
                        <Text type="secondary">- {project.description}</Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
            locale={{ emptyText: 'No projects yet' }}
          />
        )}
      </Card>

      {/* Add Member Modal */}
      <Modal
        title="Add Team Member"
        open={addMemberOpen}
        onCancel={() => setAddMemberOpen(false)}
        onOk={() => addMemberForm.submit()}
        confirmLoading={addMemberMutation.isPending}
      >
        <Form
          form={addMemberForm}
          layout="vertical"
          onFinish={(values) => addMemberMutation.mutate(values)}
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter user email' },
              { type: 'email', message: 'Please enter a valid email' },
            ]}
          >
            <Input placeholder="user@example.com" />
          </Form.Item>
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Please select a role' }]}
            initialValue="member"
          >
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Project Modal */}
      <Modal
        title="Create Project"
        open={createProjectOpen}
        onCancel={() => setCreateProjectOpen(false)}
        onOk={() => createProjectForm.submit()}
        confirmLoading={createProjectMutation.isPending}
      >
        <Form
          form={createProjectForm}
          layout="vertical"
          onFinish={(values) => createProjectMutation.mutate(values)}
        >
          <Form.Item
            name="name"
            label="Project Name"
            rules={[{ required: true, message: 'Please enter project name' }]}
          >
            <Input placeholder="My Project" />
          </Form.Item>
          <Form.Item
            name="prefix"
            label="Prefix"
            rules={[
              { required: true, message: 'Please enter a prefix' },
              { max: 5, message: 'Prefix must be 5 characters or less' },
            ]}
          >
            <Input placeholder="PROJ" style={{ textTransform: 'uppercase' }} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="Project description..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TeamPage;
