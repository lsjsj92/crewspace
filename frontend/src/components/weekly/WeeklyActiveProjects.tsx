// frontend/src/components/weekly/WeeklyActiveProjects.tsx
// 진행해야 할 프로젝트 섹션 컴포넌트

import React from 'react';
import { Typography, List } from 'antd';
import type { ActiveProjectItem } from '@/api/weekly';

const { Title, Text } = Typography;

interface WeeklyActiveProjectsProps {
  projects: ActiveProjectItem[];
}

const WeeklyActiveProjects: React.FC<WeeklyActiveProjectsProps> = ({ projects }) => {
  // Epic 제목 기준으로 중복 제거
  const uniqueEpics = Array.from(new Set(projects.map((p) => p.epic_title)));

  return (
    <div style={{ marginBottom: 24 }}>
      <Title level={5} style={{ marginBottom: 12 }}>진행해야 할 프로젝트</Title>
      {uniqueEpics.length === 0 ? (
        <Text type="secondary">진행 중인 프로젝트가 없습니다.</Text>
      ) : (
        <List
          size="small"
          dataSource={uniqueEpics}
          renderItem={(epic) => (
            <List.Item style={{ padding: '4px 0' }}>
              <Text>- {epic}</Text>
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default WeeklyActiveProjects;
