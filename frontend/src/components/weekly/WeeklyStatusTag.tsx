// frontend/src/components/weekly/WeeklyStatusTag.tsx
// 주간 뷰 상태 태그 컴포넌트

import React from 'react';
import { Tag } from 'antd';

const STATUS_COLOR_MAP: Record<string, string> = {
  '진행중': '#1890ff',
  '완료': '#52c41a',
  '지연': '#ff4d4f',
  '취소': '#8c8c8c',
  '대기중': '#faad14',
};

interface WeeklyStatusTagProps {
  status: string;
}

const WeeklyStatusTag: React.FC<WeeklyStatusTagProps> = ({ status }) => {
  const color = STATUS_COLOR_MAP[status] || '#d9d9d9';
  return <Tag color={color}>{status}</Tag>;
};

export default WeeklyStatusTag;
