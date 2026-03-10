import React from 'react';
import { Card as AntCard, Tag, Avatar, Tooltip, Typography, Space } from 'antd';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ClockCircleOutlined } from '@ant-design/icons';
import type { Card } from '@/types';
import { formatDate, isOverdue } from '@/utils/date';

const { Text } = Typography;

const CARD_TYPE_COLORS: Record<string, string> = {
  epic: '#722ed1',
  story: '#1890ff',
  task: '#52c41a',
  bug: '#f5222d',
};

const PRIORITY_COLORS: Record<string, string> = {
  lowest: '#8c8c8c',
  low: '#52c41a',
  medium: '#1890ff',
  high: '#faad14',
  highest: '#f5222d',
};

const PRIORITY_LABELS: Record<string, string> = {
  lowest: 'Lowest',
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  highest: 'Highest',
};

interface CardItemProps {
  card: Card;
  prefix: string;
  onClick: (card: Card) => void;
}

const CardItem: React.FC<CardItemProps> = ({ card, prefix, onClick }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: `card-${card.id}`,
    data: {
      type: 'card',
      card,
    },
  });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: 'grab',
    marginBottom: 8,
  };

  const overdue = isOverdue(card.due_date);

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <AntCard
        size="small"
        hoverable
        onClick={() => onClick(card)}
        style={{ borderLeft: `3px solid ${CARD_TYPE_COLORS[card.card_type] || '#d9d9d9'}` }}
        bodyStyle={{ padding: '8px 12px' }}
      >
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Tag
              color={CARD_TYPE_COLORS[card.card_type]}
              style={{ margin: 0, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}
            >
              {card.card_type.toUpperCase()}
            </Tag>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {prefix}-{card.card_number}
            </Text>
          </div>

          <Text strong style={{ fontSize: 13 }}>
            {card.title}
          </Text>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size={4}>
              <Tooltip title={PRIORITY_LABELS[card.priority] || 'Normal'}>
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: PRIORITY_COLORS[card.priority] || '#d9d9d9',
                  }}
                />
              </Tooltip>
              {card.labels?.map((cl) =>
                cl.label ? (
                  <Tag
                    key={cl.label_id}
                    color={cl.label.color}
                    style={{ margin: 0, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}
                  >
                    {cl.label.name}
                  </Tag>
                ) : null
              )}
            </Space>

            <Space size={4}>
              {card.due_date && (
                <Tooltip title={`Due: ${formatDate(card.due_date)}`}>
                  <Text
                    style={{ fontSize: 11, color: overdue ? '#f5222d' : '#8c8c8c' }}
                  >
                    <ClockCircleOutlined /> {formatDate(card.due_date)}
                  </Text>
                </Tooltip>
              )}
            </Space>
          </div>

          {card.assignees && card.assignees.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Avatar.Group size="small" maxCount={3}>
                {card.assignees.map((a) => (
                  <Tooltip
                    key={a.id}
                    title={a.user?.display_name || a.user?.username}
                  >
                    <Avatar size="small" style={{ backgroundColor: '#1890ff', fontSize: 10 }}>
                      {(a.user?.display_name || a.user?.username || '?')[0].toUpperCase()}
                    </Avatar>
                  </Tooltip>
                ))}
              </Avatar.Group>
            </div>
          )}
        </Space>
      </AntCard>
    </div>
  );
};

export default CardItem;
