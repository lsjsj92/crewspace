import React from 'react';
import { Card as AntCard, Tag, Avatar, Tooltip, Typography, Space } from 'antd';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Card, ParentCardInfo } from '@/types';
import { formatDate, isOverdue } from '@/utils/date';
import { getCardTypeColor, getCardTypeIcon, getCardTypeLabel } from '@/constants/cardTypes';

// 상위 카드 체인을 최상위(Epic)부터 순서대로 배열로 변환한다
function buildParentChain(parent: ParentCardInfo | null | undefined): ParentCardInfo[] {
  const chain: ParentCardInfo[] = [];
  let current = parent ?? null;
  while (current) {
    chain.push(current);
    current = current.parent ?? null;
  }
  return chain.reverse();
}

const { Text } = Typography;

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
  deadlineWarningDays?: number;
}

const CardItem: React.FC<CardItemProps> = ({ card, prefix, onClick, deadlineWarningDays = 3 }) => {
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
    opacity: isDragging ? 0.3 : 1,
    cursor: isDragging ? 'grabbing' : 'grab',
    marginBottom: 8,
  };

  const overdue = !card.completed_at && isOverdue(card.due_date);
  const approaching = !card.completed_at && !overdue && card.due_date
    && dayjs(card.due_date).diff(dayjs().startOf('day'), 'day') <= deadlineWarningDays;

  const dueDateColor = overdue ? '#f5222d' : approaching ? '#faad14' : '#8c8c8c';

  const parentChain = buildParentChain(card.parent);
  const parentPathText = parentChain.map((p) => p.title).join(' > ');

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <AntCard
        size="small"
        hoverable
        onClick={() => onClick(card)}
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

          {parentChain.length > 0 && (
            <Tooltip title={parentPathText}>
              <div
                style={{
                  fontSize: 10,
                  color: '#8c8c8c',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {parentChain.map((p, i) => {
                  const ParentIcon = getCardTypeIcon(p.card_type);
                  return (
                    <span key={p.id}>
                      {i > 0 && <span style={{ margin: '0 3px' }}>{'>'}</span>}
                      <ParentIcon style={{ color: getCardTypeColor(p.card_type), fontSize: 9, marginRight: 2 }} />
                      {p.title}
                    </span>
                  );
                })}
              </div>
            </Tooltip>
          )}

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
                    style={{ fontSize: 11, color: dueDateColor }}
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
