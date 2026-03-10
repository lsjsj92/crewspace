import React, { useState } from 'react';
import { Typography, Button, Badge, Input, Space } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import type { BoardColumn as BoardColumnType, Card } from '@/types';
import CardItem from './CardItem';

const { Text, Title } = Typography;

interface BoardColumnProps {
  column: BoardColumnType;
  prefix: string;
  onCardClick: (card: Card) => void;
  onAddCard: (columnId: string, title: string) => void;
}

const BoardColumn: React.FC<BoardColumnProps> = ({
  column,
  prefix,
  onCardClick,
  onAddCard,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newCardTitle, setNewCardTitle] = useState('');

  const { setNodeRef, isOver } = useDroppable({
    id: `column-${column.id}`,
    data: {
      type: 'column',
      column,
    },
  });

  const cards = column.cards || [];
  const cardCount = cards.length;
  const isOverWip = column.wip_limit !== null && cardCount > column.wip_limit;

  const handleAddCard = () => {
    if (newCardTitle.trim()) {
      onAddCard(column.id, newCardTitle.trim());
      setNewCardTitle('');
      setIsAdding(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddCard();
    } else if (e.key === 'Escape') {
      setNewCardTitle('');
      setIsAdding(false);
    }
  };

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
          items={cards.map((c) => `card-${c.id}`)}
          strategy={verticalListSortingStrategy}
        >
          {cards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              prefix={prefix}
              onClick={onCardClick}
            />
          ))}
        </SortableContext>
      </div>

      {isAdding ? (
        <div style={{ padding: '4px 4px 0' }}>
          <Input
            autoFocus
            placeholder="Enter card title..."
            value={newCardTitle}
            onChange={(e) => setNewCardTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => {
              if (!newCardTitle.trim()) {
                setIsAdding(false);
              }
            }}
          />
          <Space style={{ marginTop: 4 }}>
            <Button type="primary" size="small" onClick={handleAddCard}>
              Add
            </Button>
            <Button
              size="small"
              onClick={() => {
                setNewCardTitle('');
                setIsAdding(false);
              }}
            >
              Cancel
            </Button>
          </Space>
        </div>
      ) : (
        <Button
          type="text"
          icon={<PlusOutlined />}
          style={{ marginTop: 4 }}
          onClick={() => setIsAdding(true)}
          block
        >
          Add card
        </Button>
      )}
    </div>
  );
};

export default BoardColumn;
