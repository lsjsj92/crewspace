import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Segmented, Spin, Breadcrumb } from 'antd';
import {
  AppstoreOutlined,
  FieldTimeOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getProject } from '@/api/projects';
import KanbanBoard from '@/components/board/KanbanBoard';

const { Title } = Typography;

const ProjectBoardPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  });

  const handleViewChange = (value: string | number) => {
    if (!id) return;
    switch (value) {
      case 'Board':
        navigate(`/projects/${id}/board`);
        break;
      case 'Timeline':
        navigate(`/projects/${id}/timeline`);
        break;
      case 'Settings':
        navigate(`/projects/${id}/settings`);
        break;
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!project || !id) {
    return <div>Project not found</div>;
  }

  return (
    <div>
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: 'Dashboard', href: '/dashboard' },
          { title: project.name },
          { title: 'Board' },
        ]}
      />

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          {project.name}
        </Title>
        <Segmented
          value="Board"
          onChange={handleViewChange}
          options={[
            { label: 'Board', value: 'Board', icon: <AppstoreOutlined /> },
            { label: 'Timeline', value: 'Timeline', icon: <FieldTimeOutlined /> },
            { label: 'Settings', value: 'Settings', icon: <SettingOutlined /> },
          ]}
        />
      </div>

      <KanbanBoard
        projectId={id}
        teamId={project.team_id}
        prefix={project.prefix}
      />
    </div>
  );
};

export default ProjectBoardPage;
