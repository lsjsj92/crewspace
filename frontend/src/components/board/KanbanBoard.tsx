import React, { useState, useCallback } from 'react';
import { Spin } from 'antd';
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import type { Card } from '@/types';
import { useBoard, useMoveCard, useCreateCard } from '@/hooks/useBoard';
import BoardColumn from './BoardColumn';
import CardDetailDrawer from './CardDetailDrawer';

interface KanbanBoardProps {
  projectId: string;
  teamId?: string;
  prefix: string;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({ projectId, teamId, prefix }) => {
  const { data: columns, isLoading } = useBoard(projectId);
  const moveCardMutation = useMoveCard(projectId);
  const createCardMutation = useCreateCard(projectId);

  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || !columns) return;

      const activeData = active.data.current;
      if (!activeData || activeData.type !== 'card') return;

      const activeCard = activeData.card as Card;
      let targetColumnId: string;
      let targetPosition: number;

      const overData = over.data.current;
      if (overData?.type === 'column') {
        targetColumnId = overData.column.id;
        const targetColumn = columns.find((c) => c.id === targetColumnId);
        targetPosition = targetColumn?.cards?.length || 0;
      } else if (overData?.type === 'card') {
        const overCard = overData.card as Card;
        targetColumnId = overCard.column_id;
        const targetColumn = columns.find((c) => c.id === targetColumnId);
        const overIndex = targetColumn?.cards?.findIndex((c) => c.id === overCard.id) ?? 0;
        targetPosition = overIndex;
      } else {
        return;
      }

      if (activeCard.column_id === targetColumnId && activeCard.position === targetPosition) {
        return;
      }

      moveCardMutation.mutate({
        cardId: activeCard.id,
        data: { column_id: targetColumnId, position: targetPosition },
      });
    },
    [columns, moveCardMutation]
  );

  const handleCardClick = useCallback((card: Card) => {
    setSelectedCardId(card.id);
    setDrawerOpen(true);
  }, []);

  const handleAddCard = useCallback(
    (columnId: string, title: string) => {
      createCardMutation.mutate({
        title,
        column_id: columnId,
        card_type: 'task',
      });
    },
    [createCardMutation]
  );

  const handleCreateSubCard = useCallback(
    (parentId: string, columnId: string) => {
      const title = prompt('하위 카드 제목을 입력하세요:');
      if (title?.trim()) {
        createCardMutation.mutate({
          title: title.trim(),
          column_id: columnId,
          parent_id: parentId,
          card_type: 'task',
        });
      }
    },
    [createCardMutation]
  );

  const selectedColumnName = columns
    ?.find((c) => c.cards?.some((card) => card.id === selectedCardId))
    ?.name;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragEnd={handleDragEnd}
      >
        <div
          style={{
            display: 'flex',
            gap: 12,
            overflowX: 'auto',
            padding: '8px 0',
            minHeight: 400,
          }}
        >
          {columns?.map((column) => (
            <BoardColumn
              key={column.id}
              column={column}
              prefix={prefix}
              onCardClick={handleCardClick}
              onAddCard={handleAddCard}
            />
          ))}
        </div>
      </DndContext>

      <CardDetailDrawer
        cardId={selectedCardId}
        projectId={projectId}
        teamId={teamId}
        prefix={prefix}
        columnName={selectedColumnName}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCardId(null);
        }}
        onCreateSubCard={handleCreateSubCard}
      />
    </>
  );
};

export default KanbanBoard;
