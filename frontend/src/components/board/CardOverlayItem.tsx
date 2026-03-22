import React from 'react';
import { Card as AntCard, Tag, Avatar, Tooltip, Typography, Space } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';
import type { Card } from '@/types';
import { formatDate, isOverdue } from '@/utils/date';
import { getCardTypeColor, getCardTypeIcon, getCardTypeLabel } from '@/constants/cardTypes';

const { Text } = Typography;

const PRIORITY_COLORS: Record<string, string> = {
  lowest: '#8c8c8c',
  low: '#52c41a',
  medium: '#1890ff',
  high: '#faad14',
  highest: '#f5222d',
};

interface CardOverlayItemProps {
  card: Card;
  prefix: string;
}

const CardOverlayItem: React.FC<CardOverlayItemProps> = ({ card, prefix }) => {
  const overdue = isOverdue(card.due_date);

  return (
    <div
      style={{
        width: 268,
        transform: 'rotate(1.5deg)',
        boxShadow: '0 12px 32px rgba(0, 0, 0, 0.18)',
        opacity: 0.92,
        cursor: 'grabbing',
      }}
    >
      <AntCard
        size="small"
        style={{ borderLeft: `3px solid ${getCardTypeColor(card.card_type)}` }}
        bodyStyle={{ padding: '8px 12px' }}
      >
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Tag
              color={getCardTypeColor(card.card_type)}
              style={{ margin: 0, fontSize: 10, lineHeight: '16px', padding: '0 4px' }}
            >
              {React.createElement(getCardTypeIcon(card.card_type), { style: { marginRight: 2, fontSize: 10 } })}
              {getCardTypeLabel(card.card_type)}
            </Tag>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {prefix}-{card.card_number}
            </Text>
          </div>
          <Text strong style={{ fontSize: 13 }}>{card.title}</Text>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Tooltip title={card.priority}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: PRIORITY_COLORS[card.priority] || '#d9d9d9',
                }}
              />
            </Tooltip>
            {card.due_date && (
              <Text style={{ fontSize: 11, color: overdue ? '#f5222d' : '#8c8c8c' }}>
                <ClockCircleOutlined /> {formatDate(card.due_date)}
              </Text>
            )}
          </div>
          {card.assignees && card.assignees.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Avatar.Group size="small" maxCount={3}>
                {card.assignees.map((a) => (
                  <Avatar key={a.id} size="small" style={{ backgroundColor: '#1890ff', fontSize: 10 }}>
                    {(a.user?.display_name || a.user?.username || '?')[0].toUpperCase()}
                  </Avatar>
                ))}
              </Avatar.Group>
            </div>
          )}
        </Space>
      </AntCard>
    </div>
  );
};

export default CardOverlayItem;
