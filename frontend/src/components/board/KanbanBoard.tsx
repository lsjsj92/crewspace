import React, { useState, useCallback, useRef, useMemo } from 'react';
import { Spin, Modal, Form, Input, Select, DatePicker, Alert } from 'antd';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useQuery } from '@tanstack/react-query';
import type { Card, CardType, CardPriority } from '@/types';
import { useBoard, useMoveCard, useCreateCard } from '@/hooks/useBoard';
import { checkDuplicateTitle } from '@/api/cards';
import apiClient from '@/api/client';
import { CARD_TYPE_CONFIG, getAllowedChildTypes } from '@/constants/cardTypes';
import BoardColumn from './BoardColumn';
import CardDetailDrawer from './CardDetailDrawer';
import CardOverlayItem from './CardOverlayItem';

const PRIORITY_OPTIONS = [
  { value: 'lowest', label: 'Lowest' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'highest', label: 'Highest' },
];

interface KanbanBoardProps {
  projectId: string;
  teamId?: string;
  prefix: string;
  filters?: import('@/components/common/BoardFilterBar').BoardFilters;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({ projectId, teamId, prefix, filters }) => {
  const { data: columns, isLoading } = useBoard(projectId);
  const moveCardMutation = useMoveCard(projectId);
  const createCardMutation = useCreateCard(projectId);

  const { data: cardTypesConfig } = useQuery({
    queryKey: ['card-types-config'],
    queryFn: async () => {
      const res = await apiClient.get<{ completed_visible_days?: number }>('/card-types');
      return res.data;
    },
    staleTime: Infinity,
  });
  const completedVisibleDays = cardTypesConfig?.completed_visible_days ?? 3;

  // 필터 적용: columns의 cards를 필터링 (flat - 선택된 타입만 표시)
  const filteredColumns = useMemo(() => {
    if (!columns || !filters) return columns;
    const hasFilter = filters.cardTypes.length > 0 || filters.assigneeIds.length > 0 || filters.priorities.length > 0;
    if (!hasFilter) return columns;

    return columns.map((col) => ({
      ...col,
      cards: (col.cards || []).filter((card) => {
        if (filters.cardTypes.length > 0 && !filters.cardTypes.includes(card.card_type as CardType)) {
          return false;
        }
        if (filters.assigneeIds.length > 0) {
          const cardAssigneeIds = (card.assignees || []).map((a) => a.user_id);
          if (!filters.assigneeIds.some((id) => cardAssigneeIds.includes(id))) {
            return false;
          }
        }
        if (filters.priorities.length > 0 && !filters.priorities.includes(card.priority as CardPriority)) {
          return false;
        }
        return true;
      }),
    }));
  }, [columns, filters]);

  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeCard, setActiveCard] = useState<Card | null>(null);

  // Add card modal state
  const [createCardModalOpen, setCreateCardModalOpen] = useState(false);
  const [createCardColumnId, setCreateCardColumnId] = useState<string | null>(null);
  const [createCardForm] = Form.useForm();

  // Sub-card modal state
  const [subCardModalOpen, setSubCardModalOpen] = useState(false);
  const [subCardParentId, setSubCardParentId] = useState<string | null>(null);
  const [subCardColumnId, setSubCardColumnId] = useState<string | null>(null);
  const [subCardType, setSubCardType] = useState<CardType>('task');
  const [subCardTitle, setSubCardTitle] = useState('');
  const [subCardParentType, setSubCardParentType] = useState<string | null>(null);

  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const duplicateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const activeData = event.active.data.current;
    if (activeData?.type === 'card') {
      setActiveCard(activeData.card as Card);
    }
  }, []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      setActiveCard(null);

      const { active, over } = event;
      if (!over || !columns) return;

      const activeData = active.data.current;
      if (!activeData || activeData.type !== 'card') return;

      const draggedCard = activeData.card as Card;
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

      if (draggedCard.column_id === targetColumnId && draggedCard.position === targetPosition) {
        return;
      }

      moveCardMutation.mutate({
        cardId: draggedCard.id,
        data: { column_id: targetColumnId, position: targetPosition },
      });
    },
    [columns, moveCardMutation]
  );

  const handleCardClick = useCallback((card: Card) => {
    setSelectedCardId(card.id);
    setDrawerOpen(true);
  }, []);

  const handleTitleCheck = useCallback((title: string, cardType: string) => {
    if (duplicateTimerRef.current) {
      clearTimeout(duplicateTimerRef.current);
    }
    setDuplicateWarning(null);
    if (!title.trim() || !cardType) return;

    duplicateTimerRef.current = setTimeout(async () => {
      try {
        const result = await checkDuplicateTitle(projectId, title.trim(), cardType);
        if (result.has_duplicate) {
          const cardNums = result.cards.map(c => `${prefix}-${c.card_number}`).join(', ');
          setDuplicateWarning(`동일한 이름의 카드가 이미 존재합니다 (${cardNums}). 그래도 생성할 수 있습니다.`);
        }
      } catch {
        // 실패해도 경고만이므로 무시
      }
    }, 500);
  }, [projectId, prefix]);

  // Add card 버튼 클릭 시 Modal 열기
  const handleAddCard = useCallback((columnId: string) => {
    setCreateCardColumnId(columnId);
    createCardForm.resetFields();
    createCardForm.setFieldsValue({ card_type: 'task', priority: 'medium' });
    setCreateCardModalOpen(true);
  }, [createCardForm]);

  // Add card Modal 제출
  const handleCreateCardSubmit = useCallback((values: {
    title: string;
    card_type: CardType;
    priority?: CardPriority;
    description?: string;
    start_date?: unknown;
    due_date?: unknown;
  }) => {
    if (!createCardColumnId) return;
    const startDate = values.start_date as { format: (f: string) => string } | null;
    const dueDate = values.due_date as { format: (f: string) => string } | null;
    createCardMutation.mutate(
      {
        title: values.title,
        column_id: createCardColumnId,
        card_type: values.card_type,
        priority: values.priority,
        description: values.description,
        start_date: startDate ? startDate.format('YYYY-MM-DD') : undefined,
        due_date: dueDate ? dueDate.format('YYYY-MM-DD') : undefined,
      },
      {
        onSuccess: () => {
          setCreateCardModalOpen(false);
          createCardForm.resetFields();
          setDuplicateWarning(null);
        },
      }
    );
  }, [createCardColumnId, createCardMutation, createCardForm]);

  // Sub-card 생성 Modal 열기
  const handleCreateSubCard = useCallback(
    (parentId: string, columnId: string, parentType?: string) => {
      const allowedChildren = parentType ? getAllowedChildTypes(parentType) : ['task'];
      const childType: CardType = (allowedChildren[0] || 'task') as CardType;

      setSubCardParentId(parentId);
      setSubCardColumnId(columnId);
      setSubCardType(childType);
      setSubCardParentType(parentType || null);
      setSubCardTitle('');
      setSubCardModalOpen(true);
    },
    []
  );

  // Sub-card Modal 제출
  const handleSubCardSubmit = useCallback(async () => {
    if (!subCardTitle.trim() || !subCardParentId || !subCardColumnId || createCardMutation.isPending) return;
    try {
      await createCardMutation.mutateAsync({
        title: subCardTitle.trim(),
        column_id: subCardColumnId,
        parent_id: subCardParentId,
        card_type: subCardType,
      });
      setSubCardModalOpen(false);
      setSubCardTitle('');
    } catch {
      // Error handled by React Query
    }
  }, [subCardTitle, subCardParentId, subCardColumnId, subCardType, createCardMutation]);

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
        onDragStart={handleDragStart}
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
          {filteredColumns?.map((column) => (
            <BoardColumn
              key={column.id}
              column={column}
              prefix={prefix}
              onCardClick={handleCardClick}
              onAddCard={handleAddCard}
              completedVisibleDays={completedVisibleDays}
            />
          ))}
        </div>
        <DragOverlay dropAnimation={null}>
          {activeCard ? <CardOverlayItem card={activeCard} prefix={prefix} /> : null}
        </DragOverlay>
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
        onNavigateCard={(id) => setSelectedCardId(id)}
      />

      {/* Card 생성 Modal */}
      <Modal
        title="Add card"
        open={createCardModalOpen}
        onOk={() => createCardForm.submit()}
        onCancel={() => {
          setCreateCardModalOpen(false);
          createCardForm.resetFields();
          setDuplicateWarning(null);
        }}
        okText="Create"
        cancelText="Cancel"
        confirmLoading={createCardMutation.isPending}
      >
        <Form
          form={createCardForm}
          layout="vertical"
          onFinish={handleCreateCardSubmit}
        >
          <Form.Item
            name="title"
            label="Title"
            rules={[{ required: true, message: 'Title is required' }]}
          >
            <Input
              autoFocus
              placeholder="Card title"
              onBlur={(e) => {
                const cardType = createCardForm.getFieldValue('card_type');
                handleTitleCheck(e.target.value, cardType);
              }}
            />
          </Form.Item>
          <Form.Item name="card_type" label="Type" rules={[{ required: true }]}>
            <Select
              options={Object.entries(CARD_TYPE_CONFIG)
                .filter(([, config]) => config.canBeIndependent)
                .sort(([, a], [, b]) => a.displayOrder - b.displayOrder)
                .map(([key, config]) => ({ value: key, label: config.label }))}
              onChange={(value: string) => {
                const title = createCardForm.getFieldValue('title');
                if (title) handleTitleCheck(title, value);
              }}
            />
          </Form.Item>
          {duplicateWarning && (
            <Alert
              message={duplicateWarning}
              type="warning"
              showIcon
              closable
              onClose={() => setDuplicateWarning(null)}
              style={{ marginBottom: 16 }}
            />
          )}
          <Form.Item name="priority" label="Priority">
            <Select options={PRIORITY_OPTIONS} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} placeholder="Description (optional)" />
          </Form.Item>
          <div style={{ display: 'flex', gap: 12 }}>
            <Form.Item name="start_date" label="Start Date" style={{ flex: 1 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="due_date" label="Due Date" style={{ flex: 1 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </div>
        </Form>
      </Modal>

      {/* Sub-card 생성 Modal */}
      <Modal
        title="Create sub-card"
        open={subCardModalOpen}
        onOk={handleSubCardSubmit}
        onCancel={() => {
          setSubCardModalOpen(false);
          setSubCardTitle('');
        }}
        okText="Create"
        cancelText="Cancel"
        okButtonProps={{ disabled: !subCardTitle.trim() || createCardMutation.isPending }}
        confirmLoading={createCardMutation.isPending}
        zIndex={1100}
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Type</label>
          <Select
            value={subCardType}
            style={{ width: '100%' }}
            disabled={!subCardParentType || getAllowedChildTypes(subCardParentType).length <= 1}
            onChange={(value: CardType) => setSubCardType(value)}
            options={
              subCardParentType
                ? getAllowedChildTypes(subCardParentType).map((key) => ({
                    value: key,
                    label: CARD_TYPE_CONFIG[key]?.label || key,
                  }))
                : [{ value: subCardType, label: CARD_TYPE_CONFIG[subCardType]?.label || subCardType }]
            }
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Title</label>
          <Input
            autoFocus
            placeholder="Enter sub-card title..."
            value={subCardTitle}
            onChange={(e) => setSubCardTitle(e.target.value)}
            onPressEnter={handleSubCardSubmit}
          />
        </div>
      </Modal>
    </>
  );
};

export default KanbanBoard;
