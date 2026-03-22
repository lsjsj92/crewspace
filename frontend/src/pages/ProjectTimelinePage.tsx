import React, { useState, useMemo, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Segmented, Spin, Breadcrumb, Empty, Tag, Tooltip, Modal, Input, Select } from 'antd';
import {
  AppstoreOutlined,
  FieldTimeOutlined,
  SettingOutlined,
  RightOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { getProject, getProjectMembers } from '@/api/projects';
import { getProjectCards, createCard, reorderCard } from '@/api/cards';
import { getCardTypeColor, getCardTypeIcon, CARD_TYPE_SORT_ORDER, CARD_TYPE_CONFIG, getAllowedChildTypes } from '@/constants/cardTypes';
import CardDetailDrawer from '@/components/board/CardDetailDrawer';
import BoardFilterBar, { BoardFilters, EMPTY_FILTERS } from '@/components/common/BoardFilterBar';
import type { Card, CardType } from '@/types';

dayjs.extend(isoWeek);

const { Title } = Typography;

const WEEK_COL_WIDTH = 80;
const ROW_HEIGHT = 36;
const TASK_PANEL_WIDTH = 360;
const DEPTH_INDENT = 20;
const DEPTH_BG = [
  'transparent',
  'rgba(114, 46, 209, 0.03)',
  'rgba(24, 144, 255, 0.03)',
  'rgba(82, 196, 26, 0.03)',
  'rgba(250, 173, 20, 0.03)',
];

interface WeekInfo {
  start: dayjs.Dayjs;
  end: dayjs.Dayjs;
  label: string;
  monthLabel: string;
}

function generateWeeks(startDate: dayjs.Dayjs, endDate: dayjs.Dayjs): WeekInfo[] {
  const weeks: WeekInfo[] = [];
  let current = startDate.startOf('isoWeek');
  const end = endDate.endOf('isoWeek');

  while (current.isBefore(end) || current.isSame(end, 'day')) {
    const weekEnd = current.add(6, 'day');
    weeks.push({
      start: current,
      end: weekEnd,
      label: `${current.format('MM/DD')}`,
      monthLabel: `${current.format('YYYY-MM')}`,
    });
    current = current.add(7, 'day');
  }
  return weeks;
}

function groupWeeksByMonth(weeks: WeekInfo[]): { month: string; count: number }[] {
  const groups: { month: string; count: number }[] = [];
  for (const week of weeks) {
    const last = groups[groups.length - 1];
    if (last && last.month === week.monthLabel) {
      last.count++;
    } else {
      groups.push({ month: week.monthLabel, count: 1 });
    }
  }
  return groups;
}

interface TimelineNode {
  card: Card;
  children: TimelineNode[];
  depth: number;
}

function buildHierarchy(cards: Card[]): TimelineNode[] {
  const cardMap = new Map<string, TimelineNode>();
  const roots: TimelineNode[] = [];

  for (const card of cards) {
    cardMap.set(card.id, { card, children: [], depth: 0 });
  }

  for (const card of cards) {
    const node = cardMap.get(card.id)!;
    if (card.parent_id && cardMap.has(card.parent_id)) {
      const parent = cardMap.get(card.parent_id)!;
      node.depth = parent.depth + 1;
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }

  const sortNodes = (nodes: TimelineNode[]) => {
    nodes.sort((a, b) => {
      const posA = a.card.position ?? 0;
      const posB = b.card.position ?? 0;
      if (posA !== posB) return posA - posB;
      const orderA = CARD_TYPE_SORT_ORDER[a.card.card_type] ?? 99;
      const orderB = CARD_TYPE_SORT_ORDER[b.card.card_type] ?? 99;
      if (orderA !== orderB) return orderA - orderB;
      const dateA = a.card.start_date || a.card.due_date || '';
      const dateB = b.card.start_date || b.card.due_date || '';
      return dateA.localeCompare(dateB);
    });
    for (const node of nodes) {
      if (node.children.length > 0) sortNodes(node.children);
    }
  };
  sortNodes(roots);

  const fixDepths = (nodes: TimelineNode[], depth: number) => {
    for (const node of nodes) {
      node.depth = depth;
      fixDepths(node.children, depth + 1);
    }
  };
  fixDepths(roots, 0);

  return roots;
}

function flattenTree(nodes: TimelineNode[], expandedIds: Set<string>): TimelineNode[] {
  const result: TimelineNode[] = [];
  for (const node of nodes) {
    result.push(node);
    if (node.children.length > 0 && expandedIds.has(node.card.id)) {
      result.push(...flattenTree(node.children, expandedIds));
    }
  }
  return result;
}

function getTreeLines(flatNodes: TimelineNode[], rowIndex: number): boolean[] {
  const node = flatNodes[rowIndex];
  const lines: boolean[] = [];
  for (let d = 0; d < node.depth; d++) {
    let hasSibling = false;
    for (let i = rowIndex + 1; i < flatNodes.length; i++) {
      if (flatNodes[i].depth <= d) break;
      if (flatNodes[i].depth === d + 1) {
        hasSibling = true;
        break;
      }
    }
    lines.push(hasSibling);
  }
  return lines;
}

interface TimelineRowProps {
  node: TimelineNode;
  project: { prefix: string };
  expandedIds: Set<string>;
  flatNodes: TimelineNode[];
  rowIndex: number;
  onToggleExpand: (id: string) => void;
  onCardClick: (id: string) => void;
}

const TimelineRow: React.FC<TimelineRowProps> = ({
  node, project, expandedIds, flatNodes, rowIndex, onToggleExpand, onCardClick
}) => {
  const card = node.card;
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: card.id,
  });

  const TypeIcon = getCardTypeIcon(card.card_type);
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedIds.has(card.id);
  const treeLines = node.depth > 0 ? getTreeLines(flatNodes, rowIndex) : [];

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.3 : (card.completed_at ? 0.5 : 1),
    height: ROW_HEIGHT,
    borderBottom: '1px solid #f0f0f0',
    display: 'flex',
    alignItems: 'center',
    padding: '0 8px',
    fontSize: 12,
    background: DEPTH_BG[Math.min(node.depth, DEPTH_BG.length - 1)],
    borderLeft: node.depth > 0 ? `2px solid ${getCardTypeColor(card.card_type)}` : undefined,
    position: 'relative',
    cursor: 'grab',
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <span style={{ width: 60, color: '#8c8c8c' }}>{project.prefix}-{card.card_number}</span>
      <span style={{ width: 60 }}>
        <Tag
          color={getCardTypeColor(card.card_type)}
          style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}
        >
          <TypeIcon style={{ fontSize: 10 }} />
        </Tag>
      </span>
      <span
        style={{
          flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          textDecoration: card.completed_at ? 'line-through' : 'none',
          display: 'flex', alignItems: 'center', gap: 0,
          position: 'relative',
        }}
      >
        {node.depth > 0 && treeLines.map((hasLine, d) => (
          <span key={d} style={{ display: 'inline-block', width: DEPTH_INDENT, height: ROW_HEIGHT, position: 'relative', flexShrink: 0 }}>
            {hasLine && <span style={{ position: 'absolute', left: DEPTH_INDENT / 2, top: 0, bottom: 0, width: 1, borderLeft: '1px dashed #d9d9d9' }} />}
            {d === treeLines.length - 1 && (
              <>
                <span style={{ position: 'absolute', left: DEPTH_INDENT / 2, top: 0, height: ROW_HEIGHT / 2, width: 1, borderLeft: '1px dashed #d9d9d9' }} />
                <span style={{ position: 'absolute', left: DEPTH_INDENT / 2, top: ROW_HEIGHT / 2, width: DEPTH_INDENT / 2, height: 1, borderTop: '1px dashed #d9d9d9' }} />
              </>
            )}
          </span>
        ))}
        {hasChildren && (
          <span
            onClick={(e) => { e.stopPropagation(); onToggleExpand(card.id); }}
            style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', marginRight: 2, flexShrink: 0 }}
          >
            {isExpanded ? <DownOutlined style={{ fontSize: 10 }} /> : <RightOutlined style={{ fontSize: 10 }} />}
          </span>
        )}
        {!hasChildren && node.depth > 0 && <span style={{ width: 14, flexShrink: 0 }} />}
        <span
          style={{ cursor: 'pointer', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          onClick={(e) => { e.stopPropagation(); onCardClick(card.id); }}
        >
          {card.title}
        </span>
      </span>
      <span style={{ width: 70, textAlign: 'center', color: '#8c8c8c' }}>
        {card.start_date ? dayjs(card.start_date).format('MM/DD') : '-'}
      </span>
      <span style={{ width: 70, textAlign: 'center', color: '#8c8c8c' }}>
        {card.due_date ? dayjs(card.due_date).format('MM/DD') : '-'}
      </span>
    </div>
  );
};

const ProjectTimelinePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  });

  const { data: cards, isLoading: cardsLoading } = useQuery({
    queryKey: ['project-cards', id],
    queryFn: () => getProjectCards(id!),
    enabled: !!id,
  });

  const { data: members } = useQuery({
    queryKey: ['project-members', id],
    queryFn: () => getProjectMembers(id!),
    enabled: !!id,
  });

  const [filters, setFilters] = useState<BoardFilters>(EMPTY_FILTERS);
  const [expandedIds, setExpandedIds] = React.useState<Set<string>>(new Set());
  const initializedRef = useRef(false);

  const queryClient = useQueryClient();

  // Card detail drawer state
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Sub-card modal state
  const [subCardModalOpen, setSubCardModalOpen] = useState(false);
  const [subCardParentId, setSubCardParentId] = useState<string | null>(null);
  const [subCardType, setSubCardType] = useState<CardType>('task');
  const [subCardTitle, setSubCardTitle] = useState('');
  const [subCardParentType, setSubCardParentType] = useState<string | null>(null);

  // DnD state
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );
  const [activeDragNode, setActiveDragNode] = useState<TimelineNode | null>(null);

  const memberOptions = useMemo(() => {
    return (members || []).map((m: { user_id: string; user?: { display_name?: string; username?: string } }) => ({
      user_id: m.user_id,
      display_name: m.user?.display_name || m.user?.username || 'Unknown',
    }));
  }, [members]);

  // 필터 적용
  const filteredCards = useMemo(() => {
    if (!cards) return cards;
    const hasFilter = filters.cardTypes.length > 0 || filters.assigneeIds.length > 0 || filters.priorities.length > 0 || filters.hideCompleted;
    if (!hasFilter) return cards;

    const matchedIds = new Set<string>();

    const collectDescendants = (parentId: string) => {
      for (const card of cards) {
        if (card.parent_id === parentId && !matchedIds.has(card.id)) {
          matchedIds.add(card.id);
          collectDescendants(card.id);
        }
      }
    };

    for (const card of cards) {
      if (filters.hideCompleted && card.completed_at) continue;

      let matches = true;
      if (filters.cardTypes.length > 0 && !filters.cardTypes.includes(card.card_type as CardType)) {
        matches = false;
      }
      if (filters.assigneeIds.length > 0) {
        const cardAssigneeIds = (card.assignees || []).map((a: { user_id: string }) => a.user_id);
        if (!filters.assigneeIds.some((aid) => cardAssigneeIds.includes(aid))) {
          matches = false;
        }
      }
      if (filters.priorities.length > 0 && !filters.priorities.includes(card.priority)) {
        matches = false;
      }

      if (matches) {
        matchedIds.add(card.id);
        collectDescendants(card.id);
      }
    }

    // 상위 카드도 포함
    const addAncestors = (cardId: string) => {
      const card = cards.find((c) => c.id === cardId);
      if (card?.parent_id && !matchedIds.has(card.parent_id)) {
        matchedIds.add(card.parent_id);
        addAncestors(card.parent_id);
      }
    };
    for (const cid of [...matchedIds]) {
      addAncestors(cid);
    }

    return cards.filter((c) => matchedIds.has(c.id));
  }, [cards, filters]);

  const handleCardClick = (cardId: string) => {
    setSelectedCardId(cardId);
    setDrawerOpen(true);
  };

  const createCardMutation = useMutation({
    mutationFn: (data: { title: string; card_type: CardType; parent_id?: string }) =>
      createCard(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-cards', id] });
    },
  });

  const handleCreateSubCard = useCallback(
    (parentId: string, _columnId: string, parentType?: string) => {
      const allowedChildren = parentType ? getAllowedChildTypes(parentType) : ['task'];
      const childType: CardType = (allowedChildren[0] || 'task') as CardType;
      setSubCardParentId(parentId);
      setSubCardType(childType);
      setSubCardParentType(parentType || null);
      setSubCardTitle('');
      setSubCardModalOpen(true);
    },
    []
  );

  const handleSubCardSubmit = useCallback(async () => {
    if (!subCardTitle.trim() || !subCardParentId || createCardMutation.isPending) return;
    try {
      await createCardMutation.mutateAsync({
        title: subCardTitle.trim(),
        card_type: subCardType,
        parent_id: subCardParentId,
      });
      setSubCardModalOpen(false);
      setSubCardTitle('');
    } catch {
      // Error handled by React Query
    }
  }, [subCardTitle, subCardParentId, subCardType, createCardMutation]);

  const reorderMutation = useMutation({
    mutationFn: (data: { cardId: string; parentId?: string | null; afterCardId?: string | null }) =>
      reorderCard(data.cardId, { parent_id: data.parentId, after_card_id: data.afterCardId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-cards', id] });
    },
  });

  const handleViewChange = (value: string | number) => {
    if (!id) return;
    switch (value) {
      case 'Board': navigate(`/projects/${id}/board`); break;
      case 'Timeline': navigate(`/projects/${id}/timeline`); break;
      case 'Settings': navigate(`/projects/${id}/settings`); break;
    }
  };

  const { weeks, monthGroups, flatNodes, timelineStart } = useMemo(() => {
    if (!project || !filteredCards) {
      return { weeks: [], monthGroups: [], flatNodes: [], timelineStart: dayjs() };
    }

    const roots = buildHierarchy(filteredCards);

    let activeExpandedIds = expandedIds;
    if (!initializedRef.current) {
      const allWithChildren = new Set<string>();
      const collectExpandable = (nodes: TimelineNode[]) => {
        for (const node of nodes) {
          if (node.children.length > 0) {
            allWithChildren.add(node.card.id);
            collectExpandable(node.children);
          }
        }
      };
      collectExpandable(roots);
      if (allWithChildren.size > 0) {
        activeExpandedIds = allWithChildren;
        setExpandedIds(allWithChildren);
      }
      initializedRef.current = true;
    }

    const flat = flattenTree(roots, activeExpandedIds);

    let rangeStart = project.start_date ? dayjs(project.start_date) : null;
    let rangeEnd = project.end_date ? dayjs(project.end_date) : null;

    if (!rangeStart || !rangeEnd) {
      const allDates: dayjs.Dayjs[] = [];
      filteredCards.forEach((c) => {
        if (c.start_date) allDates.push(dayjs(c.start_date));
        if (c.due_date) allDates.push(dayjs(c.due_date));
      });
      if (allDates.length > 0) {
        const minDate = allDates.reduce((a, b) => (a.isBefore(b) ? a : b));
        const maxDate = allDates.reduce((a, b) => (a.isAfter(b) ? a : b));
        if (!rangeStart) rangeStart = minDate;
        if (!rangeEnd) rangeEnd = maxDate;
      } else {
        rangeStart = dayjs();
        rangeEnd = dayjs().add(1, 'month');
      }
    }

    rangeEnd = rangeEnd.add(1, 'month');

    const w = generateWeeks(rangeStart, rangeEnd);
    const mg = groupWeeksByMonth(w);
    const ts = w.length > 0 ? w[0].start : dayjs();

    return { weeks: w, monthGroups: mg, flatNodes: flat, timelineStart: ts };
  }, [project, filteredCards, expandedIds]);

  const toggleExpand = (cardId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(cardId)) {
        next.delete(cardId);
      } else {
        next.add(cardId);
      }
      return next;
    });
  };

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const cardId = event.active.id as string;
    const node = flatNodes.find((n) => n.card.id === cardId);
    if (node) setActiveDragNode(node);
  }, [flatNodes]);

  const handleTimelineDragEnd = useCallback((event: DragEndEvent) => {
    setActiveDragNode(null);
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    const activeNode = flatNodes.find((n) => n.card.id === activeId);
    const overNode = flatNodes.find((n) => n.card.id === overId);

    if (!activeNode || !overNode) return;

    // 같은 parent의 siblings 간에만 이동 허용
    if (activeNode.card.parent_id !== overNode.card.parent_id) return;

    const activeIdx = flatNodes.indexOf(activeNode);
    const overIdx = flatNodes.indexOf(overNode);

    // 같은 parent의 siblings만 추출
    const siblings = flatNodes.filter(
      (n) => n.card.parent_id === activeNode.card.parent_id && n.card.id !== activeId
    );
    const overSiblingIdx = siblings.findIndex((n) => n.card.id === overId);

    let afterCardId: string | null = null;
    if (activeIdx < overIdx) {
      // 아래로 이동: over 뒤에 배치
      afterCardId = overId;
    } else {
      // 위로 이동: over 앞에 배치 = over 이전 sibling 뒤에 배치
      afterCardId = overSiblingIdx > 0 ? siblings[overSiblingIdx - 1].card.id : null;
    }

    reorderMutation.mutate({
      cardId: activeId,
      parentId: activeNode.card.parent_id,
      afterCardId,
    });
  }, [flatNodes, reorderMutation]);

  if (projectLoading || cardsLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spin size="large" /></div>;
  }

  if (!project || !id) return <div>Project not found</div>;

  const totalWidth = weeks.length * WEEK_COL_WIDTH;

  const getBarStyle = (card: Card, depth: number = 0): React.CSSProperties | null => {
    const start = card.start_date ? dayjs(card.start_date) : null;
    const end = card.due_date ? dayjs(card.due_date) : null;

    if (!start && !end) return null;

    const barStart = start || end!;
    const barEnd = end || start!;

    const startOffset = barStart.diff(timelineStart, 'day');
    const duration = Math.max(barEnd.diff(barStart, 'day') + 1, 1);
    const totalDays = weeks.length * 7;

    const leftPx = (startOffset / totalDays) * totalWidth;
    const widthPx = (duration / totalDays) * totalWidth;
    const barHeight = Math.max(ROW_HEIGHT - 12 - depth * 2, 12);

    return {
      position: 'absolute',
      left: Math.max(leftPx, 0),
      width: Math.min(widthPx, totalWidth - Math.max(leftPx, 0)),
      top: (ROW_HEIGHT - barHeight) / 2,
      height: barHeight,
      backgroundColor: getCardTypeColor(card.card_type),
      opacity: card.completed_at ? 0.5 : 0.85,
      borderRadius: 4,
      cursor: 'pointer',
    };
  };

  const today = dayjs();
  const todayOffset = today.diff(timelineStart, 'day');
  const todayLeft = (todayOffset / (weeks.length * 7)) * totalWidth;
  const showTodayLine = todayLeft >= 0 && todayLeft <= totalWidth;

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 16 }} items={[
        { title: 'Dashboard', href: '/dashboard' },
        { title: project.name },
        { title: 'Timeline' },
      ]} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>{project.name} - Timeline</Title>
        <Segmented
          value="Timeline"
          onChange={handleViewChange}
          options={[
            { label: 'Board', value: 'Board', icon: <AppstoreOutlined /> },
            { label: 'Timeline', value: 'Timeline', icon: <FieldTimeOutlined /> },
            { label: 'Settings', value: 'Settings', icon: <SettingOutlined /> },
          ]}
        />
      </div>

      <BoardFilterBar
        filters={filters}
        onFilterChange={setFilters}
        members={memberOptions}
        showCompletedToggle
      />

      {flatNodes.length === 0 ? (
        <Empty description="No cards in this project." />
      ) : (
        <div style={{ border: '1px solid #f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ display: 'flex' }}>
            {/* Left panel: task list */}
            <div style={{ minWidth: TASK_PANEL_WIDTH, maxWidth: TASK_PANEL_WIDTH, borderRight: '2px solid #e8e8e8', flexShrink: 0 }}>
              <div style={{ height: 28, borderBottom: '1px solid #f0f0f0', background: '#fafafa' }} />
              <div style={{
                height: 28, borderBottom: '2px solid #e8e8e8', background: '#fafafa',
                display: 'flex', alignItems: 'center', padding: '0 8px',
                fontWeight: 600, fontSize: 12, color: '#595959',
              }}>
                <span style={{ width: 60 }}>No.</span>
                <span style={{ width: 60 }}>Type</span>
                <span style={{ flex: 1 }}>Title</span>
                <span style={{ width: 70, textAlign: 'center' }}>Start</span>
                <span style={{ width: 70, textAlign: 'center' }}>Due</span>
              </div>
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragEnd={handleTimelineDragEnd}
              >
                <SortableContext items={flatNodes.map((n) => n.card.id)} strategy={verticalListSortingStrategy}>
                  {flatNodes.map((node, rowIndex) => (
                    <TimelineRow
                      key={node.card.id}
                      node={node}
                      project={project}
                      expandedIds={expandedIds}
                      flatNodes={flatNodes}
                      rowIndex={rowIndex}
                      onToggleExpand={toggleExpand}
                      onCardClick={handleCardClick}
                    />
                  ))}
                </SortableContext>
                <DragOverlay dropAnimation={null}>
                  {activeDragNode && (
                    <div style={{
                      height: ROW_HEIGHT,
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0 8px',
                      fontSize: 12,
                      background: '#fff',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                      borderRadius: 4,
                      width: TASK_PANEL_WIDTH - 16,
                      opacity: 0.92,
                    }}>
                      <Tag
                        color={getCardTypeColor(activeDragNode.card.card_type)}
                        style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0, marginRight: 8 }}
                      >
                        {React.createElement(getCardTypeIcon(activeDragNode.card.card_type), { style: { fontSize: 10 } })}
                      </Tag>
                      <span style={{ fontSize: 12 }}>{project.prefix}-{activeDragNode.card.card_number}: {activeDragNode.card.title}</span>
                    </div>
                  )}
                </DragOverlay>
              </DndContext>
            </div>

            {/* Right panel: Gantt chart area */}
            <div style={{ flex: 1, overflowX: 'auto' }}>
              <div style={{ minWidth: totalWidth }}>
                {/* Month header */}
                <div style={{ display: 'flex', height: 28, background: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
                  {monthGroups.map((mg, i) => (
                    <div
                      key={i}
                      style={{
                        width: mg.count * WEEK_COL_WIDTH,
                        textAlign: 'center',
                        fontWeight: 600,
                        fontSize: 12,
                        lineHeight: '28px',
                        borderRight: '1px solid #f0f0f0',
                        color: '#262626',
                      }}
                    >
                      {mg.month}
                    </div>
                  ))}
                </div>
                {/* Week header */}
                <div style={{ display: 'flex', height: 28, background: '#fafafa', borderBottom: '2px solid #e8e8e8' }}>
                  {weeks.map((w, i) => (
                    <div
                      key={i}
                      style={{
                        width: WEEK_COL_WIDTH,
                        textAlign: 'center',
                        fontSize: 11,
                        lineHeight: '28px',
                        borderRight: '1px solid #f0f0f0',
                        color: '#595959',
                      }}
                    >
                      {w.label}
                    </div>
                  ))}
                </div>
                {/* Gantt rows */}
                <div style={{ position: 'relative' }}>
                  {flatNodes.map((node, rowIndex) => {
                    const card = node.card;
                    const barStyle = getBarStyle(card, node.depth);
                    return (
                      <div
                        key={card.id}
                        style={{
                          height: ROW_HEIGHT,
                          borderBottom: '1px solid #f0f0f0',
                          position: 'relative',
                          background: rowIndex % 2 === 0 ? '#fff' : '#fafafa',
                        }}
                      >
                        {weeks.map((_, wi) => (
                          <div
                            key={wi}
                            style={{
                              position: 'absolute',
                              left: wi * WEEK_COL_WIDTH,
                              top: 0,
                              bottom: 0,
                              width: 1,
                              backgroundColor: '#f0f0f0',
                            }}
                          />
                        ))}
                        {barStyle && (
                          <Tooltip
                            title={
                              <div>
                                <div>{project.prefix}-{card.card_number}: {card.title}</div>
                                <div>
                                  {card.start_date && dayjs(card.start_date).format('YYYY-MM-DD')}
                                  {card.start_date && card.due_date && ' ~ '}
                                  {card.due_date && dayjs(card.due_date).format('YYYY-MM-DD')}
                                </div>
                                {card.completed_at && <div>Completed</div>}
                              </div>
                            }
                          >
                            <div
                              style={barStyle}
                              onClick={() => handleCardClick(card.id)}
                            />
                          </Tooltip>
                        )}
                      </div>
                    );
                  })}
                  {showTodayLine && (
                    <div
                      style={{
                        position: 'absolute',
                        left: todayLeft,
                        top: 0,
                        bottom: 0,
                        width: 2,
                        backgroundColor: '#ff4d4f',
                        zIndex: 10,
                        pointerEvents: 'none',
                      }}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Card detail drawer */}
      <CardDetailDrawer
        cardId={selectedCardId}
        projectId={id}
        prefix={project.prefix}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCardId(null);
        }}
        onCreateSubCard={handleCreateSubCard}
        onNavigateCard={(cardId) => setSelectedCardId(cardId)}
      />

      {/* Sub-card creation modal */}
      <Modal
        title="하위 카드 생성"
        open={subCardModalOpen}
        onOk={handleSubCardSubmit}
        onCancel={() => {
          setSubCardModalOpen(false);
          setSubCardTitle('');
        }}
        okText="생성"
        cancelText="취소"
        okButtonProps={{ disabled: !subCardTitle.trim() || createCardMutation.isPending }}
        confirmLoading={createCardMutation.isPending}
        zIndex={1100}
      >
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>타입</label>
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
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>제목</label>
          <Input
            autoFocus
            placeholder="하위 카드 제목 입력..."
            value={subCardTitle}
            onChange={(e) => setSubCardTitle(e.target.value)}
            onPressEnter={handleSubCardSubmit}
          />
        </div>
      </Modal>
    </div>
  );
};

export default ProjectTimelinePage;
