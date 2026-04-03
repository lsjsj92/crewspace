// frontend/src/components/weekly/WeeklyMonthlyGoals.tsx
// 월간 목표 섹션 컴포넌트

import React from 'react';
import { Typography, List } from 'antd';
import type { MonthlyGoalGroup } from '@/api/weekly';
import WeeklyStatusTag from '@/components/weekly/WeeklyStatusTag';

const { Title, Text } = Typography;

interface WeeklyMonthlyGoalsProps {
  month: number;
  goals: MonthlyGoalGroup[];
}

const WeeklyMonthlyGoals: React.FC<WeeklyMonthlyGoalsProps> = ({ month, goals }) => {
  const items = goals.flatMap((group) =>
    group.items.map((item) => ({
      epicTitle: group.epic_title,
      title: item.title,
      status: item.status,
    }))
  );

  return (
    <div style={{ marginBottom: 24 }}>
      <Title level={5} style={{ marginBottom: 12 }}>[{month}월] 월간 목표</Title>
      {items.length === 0 ? (
        <Text type="secondary">등록된 목표가 없습니다.</Text>
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item style={{ padding: '6px 0', display: 'flex', justifyContent: 'space-between' }}>
              <Text>
                <Text strong>[{item.epicTitle}]</Text> {item.title}
              </Text>
              <WeeklyStatusTag status={item.status} />
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default WeeklyMonthlyGoals;
