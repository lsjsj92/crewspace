import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Segmented, Spin, Breadcrumb } from 'antd';
import {
  AppstoreOutlined,
  FieldTimeOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { getProject, getProjectMembers } from '@/api/projects';
import KanbanBoard from '@/components/board/KanbanBoard';
import BoardFilterBar, { BoardFilters, EMPTY_FILTERS } from '@/components/common/BoardFilterBar';

const { Title } = Typography;

const ProjectBoardPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  });

  const { data: members } = useQuery({
    queryKey: ['project-members', id],
    queryFn: () => getProjectMembers(id!),
    enabled: !!id,
  });

  const [filters, setFilters] = useState<BoardFilters>(EMPTY_FILTERS);

  const memberOptions = useMemo(() => {
    return (members || []).map((m: { user_id: string; user?: { display_name?: string; username?: string } }) => ({
      user_id: m.user_id,
      display_name: m.user?.display_name || m.user?.username || 'Unknown',
    }));
  }, [members]);

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

      <BoardFilterBar
        filters={filters}
        onFilterChange={setFilters}
        members={memberOptions}
      />

      <KanbanBoard
        projectId={id}
        teamId={project.team_id}
        prefix={project.prefix}
        filters={filters}
      />
    </div>
  );
};

export default ProjectBoardPage;
