// frontend/src/components/weekly/WeeklyCardList.tsx
// 주간 카드 목록 공통 컴포넌트 (지난 주 / 이번 주 공용)

import React from 'react';
import { Typography, List } from 'antd';
import type { WeeklyCardItem } from '@/api/weekly';
import WeeklyStatusTag from '@/components/weekly/WeeklyStatusTag';

const { Title, Text } = Typography;

interface WeeklyCardListProps {
  title: string;
  items: WeeklyCardItem[];
}

function formatDueDate(dateStr: string | null): string {
  if (!dateStr) return '';
  return `(~${dateStr.replace(/-/g, '.')})`;
}

function buildHierarchyText(item: WeeklyCardItem): string {
  const parts: string[] = [];
  if (item.epic_title) parts.push(item.epic_title);
  if (item.story_title) parts.push(item.story_title);
  parts.push(item.task_title);
  return parts.join(' - ');
}

const WeeklyCardList: React.FC<WeeklyCardListProps> = ({ title, items }) => {
  return (
    <div style={{ marginBottom: 24 }}>
      <Title level={5} style={{ marginBottom: 12 }}>{title}</Title>
      {items.length === 0 ? (
        <Text type="secondary">해당 항목이 없습니다.</Text>
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item style={{ padding: '6px 0', display: 'flex', justifyContent: 'space-between' }}>
              <Text style={{ flex: 1 }}>
                {buildHierarchyText(item)}
                <Text type="secondary" style={{ marginLeft: 4 }}>
                  {formatDueDate(item.due_date)}
                </Text>
              </Text>
              <WeeklyStatusTag status={item.status} />
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default WeeklyCardList;
