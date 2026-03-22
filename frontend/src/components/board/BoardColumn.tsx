import React, { useMemo, useState } from 'react';
import { Typography, Button, Badge, Space } from 'antd';
import { PlusOutlined, DownOutlined } from '@ant-design/icons';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import dayjs from 'dayjs';
import type { BoardColumn as BoardColumnType, Card } from '@/types';
import CardItem from './CardItem';

const { Text, Title } = Typography;

interface BoardColumnProps {
  column: BoardColumnType;
  prefix: string;
  onCardClick: (card: Card) => void;
  onAddCard: (columnId: string) => void;
  completedVisibleDays?: number;
}

const BoardColumn: React.FC<BoardColumnProps> = ({
  column,
  prefix,
  onCardClick,
  onAddCard,
  completedVisibleDays = 3,
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${column.id}`,
    data: {
      type: 'column',
      column,
    },
  });
  const [showOlder, setShowOlder] = useState(false);

  const allCards = column.cards || [];

  // End column: 최근 완료 카드와 오래된 완료 카드 분리
  const { visibleCards, olderCompletedCards } = useMemo(() => {
    if (!column.is_end || completedVisibleDays <= 0) {
      return { visibleCards: allCards, olderCompletedCards: [] };
    }
    const cutoff = dayjs().subtract(completedVisibleDays, 'day');
    const visible: Card[] = [];
    const older: Card[] = [];
    for (const card of allCards) {
      if (card.completed_at && dayjs(card.completed_at).isBefore(cutoff)) {
        older.push(card);
      } else {
        visible.push(card);
      }
    }
    return { visibleCards: visible, olderCompletedCards: older };
  }, [allCards, column.is_end, completedVisibleDays]);

  const cardCount = allCards.length;
  const isOverWip = column.wip_limit !== null && cardCount > column.wip_limit;

  return (
    <div
      style={{
        width: 280,
        minWidth: 280,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: isOver ? '#e6f7ff' : '#f5f5f5',
        borderRadius: 8,
        padding: 8,
        maxHeight: 'calc(100vh - 220px)',
        transition: 'background-color 0.2s',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
          padding: '4px 8px',
        }}
      >
        <Space size={8}>
          <Title level={5} style={{ margin: 0, fontSize: 14 }}>
            {column.name}
          </Title>
          <Badge
            count={cardCount}
            style={{
              backgroundColor: isOverWip ? '#f5222d' : '#d9d9d9',
              color: isOverWip ? '#fff' : '#595959',
              fontSize: 11,
            }}
          />
        </Space>
        {column.wip_limit !== null && (
          <Text
            type={isOverWip ? 'danger' : 'secondary'}
            style={{ fontSize: 11 }}
          >
            WIP: {cardCount}/{column.wip_limit}
          </Text>
        )}
      </div>

      <div
        ref={setNodeRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          minHeight: 100,
          padding: '0 4px',
        }}
      >
        <SortableContext
          items={visibleCards.map((c) => `card-${c.id}`)}
          strategy={verticalListSortingStrategy}
        >
          {visibleCards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              prefix={prefix}
              onClick={onCardClick}
            />
          ))}
        </SortableContext>
        {olderCompletedCards.length > 0 && (
          <div style={{ marginTop: 4 }}>
            <Button
              type="text"
              size="small"
              icon={<DownOutlined rotate={showOlder ? 180 : 0} style={{ fontSize: 10, transition: 'transform 0.2s' }} />}
              onClick={() => setShowOlder(!showOlder)}
              style={{ width: '100%', color: '#8c8c8c', fontSize: 12 }}
            >
              {showOlder ? '숨기기' : `완료된 카드 (${olderCompletedCards.length}건)`}
            </Button>
            {showOlder && olderCompletedCards.map((card) => (
              <CardItem
                key={card.id}
                card={card}
                prefix={prefix}
                onClick={onCardClick}
              />
            ))}
          </div>
        )}
      </div>

      <Button
        type="text"
        icon={<PlusOutlined />}
        style={{ marginTop: 4 }}
        onClick={() => onAddCard(column.id)}
        block
      >
        Add card
      </Button>
    </div>
  );
};

export default BoardColumn;
