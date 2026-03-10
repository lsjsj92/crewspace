import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Segmented, Spin, Breadcrumb, Empty, Tag, Tooltip } from 'antd';
import {
  AppstoreOutlined,
  FieldTimeOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import { getProject } from '@/api/projects';
import { getProjectCards } from '@/api/cards';
import type { Card } from '@/types';

dayjs.extend(isoWeek);

const { Title } = Typography;

const CARD_TYPE_COLORS: Record<string, string> = {
  epic: '#722ed1',
  story: '#1890ff',
  task: '#52c41a',
};

const WEEK_COL_WIDTH = 80;
const ROW_HEIGHT = 36;
const TASK_PANEL_WIDTH = 360;

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

function sortCards(cards: Card[]): Card[] {
  const typeOrder: Record<string, number> = { epic: 0, story: 1, task: 2 };
  return [...cards].sort((a, b) => {
    const typeA = typeOrder[a.card_type] ?? 3;
    const typeB = typeOrder[b.card_type] ?? 3;
    if (typeA !== typeB) return typeA - typeB;
    const dateA = a.start_date || a.due_date || '';
    const dateB = b.start_date || b.due_date || '';
    return dateA.localeCompare(dateB);
  });
}

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

  const handleViewChange = (value: string | number) => {
    if (!id) return;
    switch (value) {
      case 'Board': navigate(`/projects/${id}/board`); break;
      case 'Timeline': navigate(`/projects/${id}/timeline`); break;
      case 'Settings': navigate(`/projects/${id}/settings`); break;
    }
  };

  const { weeks, monthGroups, sortedCards, timelineStart } = useMemo(() => {
    if (!project || !cards) {
      return { weeks: [], monthGroups: [], sortedCards: [], timelineStart: dayjs() };
    }

    // Determine timeline range from project dates, falling back to card dates
    let rangeStart = project.start_date ? dayjs(project.start_date) : null;
    let rangeEnd = project.end_date ? dayjs(project.end_date) : null;

    // If project has no dates, derive from cards
    if (!rangeStart || !rangeEnd) {
      const allDates: dayjs.Dayjs[] = [];
      cards.forEach((c) => {
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

    // Extend end by 1 month
    rangeEnd = rangeEnd.add(1, 'month');

    const w = generateWeeks(rangeStart, rangeEnd);
    const mg = groupWeeksByMonth(w);
    const sc = sortCards(cards);
    const ts = w.length > 0 ? w[0].start : dayjs();

    return { weeks: w, monthGroups: mg, sortedCards: sc, timelineStart: ts };
  }, [project, cards]);

  if (projectLoading || cardsLoading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}><Spin size="large" /></div>;
  }

  if (!project || !id) return <div>Project not found</div>;

  const totalWidth = weeks.length * WEEK_COL_WIDTH;

  const getBarStyle = (card: Card): React.CSSProperties | null => {
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

    return {
      position: 'absolute',
      left: Math.max(leftPx, 0),
      width: Math.min(widthPx, totalWidth - Math.max(leftPx, 0)),
      top: 6,
      height: ROW_HEIGHT - 12,
      backgroundColor: CARD_TYPE_COLORS[card.card_type] || '#d9d9d9',
      opacity: card.completed_at ? 0.5 : 0.85,
      borderRadius: 4,
      cursor: 'pointer',
    };
  };

  // Find today line position
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

      {sortedCards.length === 0 ? (
        <Empty description="No cards in this project." />
      ) : (
        <div style={{ border: '1px solid #f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ display: 'flex' }}>
            {/* Left panel: task list */}
            <div style={{ minWidth: TASK_PANEL_WIDTH, maxWidth: TASK_PANEL_WIDTH, borderRight: '2px solid #e8e8e8', flexShrink: 0 }}>
              {/* Header placeholder for month row */}
              <div style={{ height: 28, borderBottom: '1px solid #f0f0f0', background: '#fafafa' }} />
              {/* Header placeholder for week row */}
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
              {/* Task rows */}
              {sortedCards.map((card) => (
                <div
                  key={card.id}
                  style={{
                    height: ROW_HEIGHT,
                    borderBottom: '1px solid #f0f0f0',
                    display: 'flex',
                    alignItems: 'center',
                    padding: '0 8px',
                    fontSize: 12,
                    opacity: card.completed_at ? 0.5 : 1,
                  }}
                >
                  <span style={{ width: 60, color: '#8c8c8c' }}>{project.prefix}-{card.card_number}</span>
                  <span style={{ width: 60 }}>
                    <Tag
                      color={CARD_TYPE_COLORS[card.card_type]}
                      style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}
                    >
                      {card.card_type.charAt(0).toUpperCase()}
                    </Tag>
                  </span>
                  <span style={{
                    flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    textDecoration: card.completed_at ? 'line-through' : 'none',
                  }}>
                    {card.title}
                  </span>
                  <span style={{ width: 70, textAlign: 'center', color: '#8c8c8c' }}>
                    {card.start_date ? dayjs(card.start_date).format('MM/DD') : '-'}
                  </span>
                  <span style={{ width: 70, textAlign: 'center', color: '#8c8c8c' }}>
                    {card.due_date ? dayjs(card.due_date).format('MM/DD') : '-'}
                  </span>
                </div>
              ))}
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
                  {sortedCards.map((card, rowIndex) => {
                    const barStyle = getBarStyle(card);
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
                        {/* Week grid lines */}
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
                        {/* Bar */}
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
                            <div style={barStyle} />
                          </Tooltip>
                        )}
                      </div>
                    );
                  })}
                  {/* Today line */}
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
    </div>
  );
};

export default ProjectTimelinePage;
