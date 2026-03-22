import React from 'react';
import { Select, Space, Button, Switch, Typography } from 'antd';
import { FilterOutlined, ClearOutlined } from '@ant-design/icons';
import type { CardType, CardPriority } from '@/types';
import { CARD_TYPE_CONFIG } from '@/constants/cardTypes';

const { Text } = Typography;

const PRIORITY_OPTIONS = [
  { value: 'lowest', label: 'Lowest', color: '#8c8c8c' },
  { value: 'low', label: 'Low', color: '#52c41a' },
  { value: 'medium', label: 'Medium', color: '#1890ff' },
  { value: 'high', label: 'High', color: '#faad14' },
  { value: 'highest', label: 'Highest', color: '#f5222d' },
];

export interface BoardFilters {
  cardTypes: CardType[];
  assigneeIds: string[];
  priorities: CardPriority[];
  hideCompleted: boolean;
}

export const EMPTY_FILTERS: BoardFilters = {
  cardTypes: [],
  assigneeIds: [],
  priorities: [],
  hideCompleted: false,
};

interface MemberOption {
  user_id: string;
  display_name: string;
}

interface BoardFilterBarProps {
  filters: BoardFilters;
  onFilterChange: (filters: BoardFilters) => void;
  members?: MemberOption[];
  showCompletedToggle?: boolean;
}

const BoardFilterBar: React.FC<BoardFilterBarProps> = ({
  filters,
  onFilterChange,
  members = [],
  showCompletedToggle = false,
}) => {
  const hasFilters =
    filters.cardTypes.length > 0 ||
    filters.assigneeIds.length > 0 ||
    filters.priorities.length > 0 ||
    filters.hideCompleted;

  const cardTypeOptions = Object.entries(CARD_TYPE_CONFIG)
    .sort(([, a], [, b]) => a.displayOrder - b.displayOrder)
    .map(([key, config]) => ({
      value: key,
      label: config.label,
    }));

  return (
    <div style={{ marginBottom: 12, padding: '8px 0' }}>
      <Space wrap size={8} align="center">
        <FilterOutlined style={{ color: '#8c8c8c' }} />
        <Select
          mode="multiple"
          placeholder="카드 타입"
          style={{ minWidth: 140 }}
          size="small"
          value={filters.cardTypes}
          onChange={(values: CardType[]) => onFilterChange({ ...filters, cardTypes: values })}
          options={cardTypeOptions}
          maxTagCount={1}
          maxTagPlaceholder={(omitted) => `+${omitted.length}`}
          allowClear
        />
        <Select
          mode="multiple"
          placeholder="담당자"
          style={{ minWidth: 140 }}
          size="small"
          value={filters.assigneeIds}
          onChange={(values: string[]) => onFilterChange({ ...filters, assigneeIds: values })}
          options={members.map((m) => ({ value: m.user_id, label: m.display_name }))}
          maxTagCount={1}
          maxTagPlaceholder={(omitted) => `+${omitted.length}`}
          allowClear
          optionFilterProp="label"
        />
        <Select
          mode="multiple"
          placeholder="우선순위"
          style={{ minWidth: 120 }}
          size="small"
          value={filters.priorities}
          onChange={(values: CardPriority[]) => onFilterChange({ ...filters, priorities: values })}
          options={PRIORITY_OPTIONS}
          maxTagCount={1}
          maxTagPlaceholder={(omitted) => `+${omitted.length}`}
          allowClear
        />
        {showCompletedToggle && (
          <Space size={4}>
            <Text style={{ fontSize: 12, color: '#8c8c8c' }}>완료 숨김</Text>
            <Switch
              size="small"
              checked={filters.hideCompleted}
              onChange={(checked) => onFilterChange({ ...filters, hideCompleted: checked })}
            />
          </Space>
        )}
        {hasFilters && (
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={() => onFilterChange({ ...EMPTY_FILTERS })}
            style={{ color: '#8c8c8c' }}
          >
            초기화
          </Button>
        )}
      </Space>
    </div>
  );
};

export default BoardFilterBar;
