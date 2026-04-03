// frontend/src/pages/WeeklyPage.tsx
// 주간 뷰 페이지

import React, { useState, useCallback, useMemo } from 'react';
import {
  Button,
  Spin,
  Alert,
  Card,
  Dropdown,
} from 'antd';
import {
  LeftOutlined,
  RightOutlined,
  DownloadOutlined,
  FileTextOutlined,
  FileMarkdownOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import dayjs from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import { useWeekly } from '@/hooks/useWeekly';
import WeeklyMonthlyGoals from '@/components/weekly/WeeklyMonthlyGoals';
import WeeklyActiveProjects from '@/components/weekly/WeeklyActiveProjects';
import WeeklyCardList from '@/components/weekly/WeeklyCardList';
import { downloadWeeklyTemplate } from '@/utils/weeklyTemplate';

dayjs.extend(isoWeek);

function getMonday(d: dayjs.Dayjs): dayjs.Dayjs {
  return d.isoWeekday(1);
}

function isCurrentWeek(monday: dayjs.Dayjs): boolean {
  const todayMonday = getMonday(dayjs());
  return monday.isSame(todayMonday, 'day');
}

const WeeklyPage: React.FC = () => {
  const [weekMonday, setWeekMonday] = useState<dayjs.Dayjs>(() => getMonday(dayjs()));

  const weekStart = useMemo(() => weekMonday.format('YYYY-MM-DD'), [weekMonday]);
  const weekFriday = useMemo(() => weekMonday.add(4, 'day'), [weekMonday]);

  const { data, isLoading, isError, error } = useWeekly(weekStart);

  const handlePrevWeek = useCallback(() => {
    setWeekMonday((prev) => prev.subtract(7, 'day'));
  }, []);

  const handleNextWeek = useCallback(() => {
    setWeekMonday((prev) => prev.add(7, 'day'));
  }, []);

  const handleDownload = useCallback(
    (format: 'txt' | 'md') => {
      if (!data) return;
      downloadWeeklyTemplate(data, format);
    },
    [data],
  );

  const downloadMenuItems: MenuProps['items'] = [
    {
      key: 'txt',
      icon: <FileTextOutlined />,
      label: '텍스트 파일 (.txt)',
    },
    {
      key: 'md',
      icon: <FileMarkdownOutlined />,
      label: '마크다운 (.md)',
    },
  ];

  const handleDownloadMenuClick: MenuProps['onClick'] = ({ key }) => {
    handleDownload(key as 'txt' | 'md');
  };

  const weekLabel = `${weekMonday.format('YYYY.MM.DD')} ~ ${weekFriday.format('YYYY.MM.DD')}`;

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        marginBottom: 24,
        gap: 8,
      }}>
        <Button icon={<LeftOutlined />} onClick={handlePrevWeek} />
        <span style={{ fontSize: 18, fontWeight: 600, whiteSpace: 'nowrap' }}>
          {weekLabel}
        </span>
        {isCurrentWeek(weekMonday) && (
          <span style={{
            fontSize: 13,
            color: '#1890ff',
            fontWeight: 400,
            whiteSpace: 'nowrap',
            padding: '2px 8px',
            background: '#e6f4ff',
            borderRadius: 4,
          }}>
            이번 주
          </span>
        )}
        <Button icon={<RightOutlined />} onClick={handleNextWeek} />
        <div style={{ flex: 1 }} />
        <Dropdown.Button
          icon={<DownloadOutlined />}
          menu={{ items: downloadMenuItems, onClick: handleDownloadMenuClick }}
          onClick={() => handleDownload('txt')}
          disabled={!data}
        >
          다운로드
        </Dropdown.Button>
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" />
        </div>
      )}

      {isError && (
        <Alert
          type="error"
          message="주간 뷰 데이터를 불러오지 못했습니다."
          description={error instanceof Error ? error.message : '알 수 없는 오류'}
          showIcon
        />
      )}

      {data && (
        <>
          <Card style={{ marginBottom: 16 }}>
            <WeeklyMonthlyGoals month={data.month} goals={data.monthly_goals} />
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <WeeklyActiveProjects projects={data.active_projects} />
          </Card>

          <Card style={{ marginBottom: 16 }}>
            <WeeklyCardList title="지난 주 목표 및 달성 현황" items={data.last_week_items} />
          </Card>

          <Card>
            <WeeklyCardList title="주간 목표" items={data.this_week_items} />
          </Card>
        </>
      )}
    </div>
  );
};

export default WeeklyPage;
