import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Row, Col, Card, Statistic, Tag, Space, Spin, Empty, Alert, List, Collapse,
} from 'antd';
import {
  ProjectOutlined, CheckSquareOutlined, FileTextOutlined, WarningOutlined, ClockCircleOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getDashboardOverview, getMyCards } from '@/api/dashboard';
import type { CardWithProject } from '@/api/dashboard';
import { getCardTypeColor, getCardTypeIcon, getCardTypeLabel } from '@/constants/cardTypes';

const { Title, Text } = Typography;

function groupByProject(cards: CardWithProject[]): Map<string, CardWithProject[]> {
  const grouped = new Map<string, CardWithProject[]>();
  for (const card of cards) {
    const key = card.project_name;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(card);
  }
  return grouped;
}

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: getDashboardOverview,
  });

  const { data: myCardsData } = useQuery({
    queryKey: ['my-cards'],
    queryFn: getMyCards,
  });

  const myCards = myCardsData?.cards || [];
  const today = dayjs().startOf('day');

  const overdueCards = myCards.filter(
    (card) => card.due_date && dayjs(card.due_date).isBefore(today, 'day') && !card.completed_at,
  );

  const approachingCards = myCards.filter((card) => {
    if (!card.due_date || card.completed_at) return false;
    const dueDate = dayjs(card.due_date);
    const remaining = dueDate.diff(today, 'day');
    if (remaining < 0) return false;
    const startDate = card.start_date || card.created_at;
    const total = dueDate.diff(dayjs(startDate), 'day');
    if (total <= 0) return false;
    return (remaining / total) <= 0.2;
  });

  const overdueGrouped = useMemo(() => groupByProject(overdueCards), [overdueCards]);
  const approachingGrouped = useMemo(() => groupByProject(approachingCards), [approachingCards]);

  if (overviewLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const renderCardItem = (card: CardWithProject, suffix: string, suffixColor: string) => {
    const TypeIcon = getCardTypeIcon(card.card_type);
    return (
      <List.Item style={{ padding: '6px 0' }}>
        <Space size={4} wrap>
          <Tag
            color={getCardTypeColor(card.card_type)}
            style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}
          >
            <TypeIcon style={{ fontSize: 10, marginRight: 2 }} />
            {getCardTypeLabel(card.card_type)}
          </Tag>
          {card.parent_title && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {card.parent_title} &gt;
            </Text>
          )}
          <Text style={{ fontSize: 13 }}>{card.title}</Text>
          <Text style={{ fontSize: 12, color: suffixColor }}>{suffix}</Text>
        </Space>
      </List.Item>
    );
  };

  const renderGroupedAlert = (
    grouped: Map<string, CardWithProject[]>,
    totalCount: number,
    alertMessage: string,
    alertType: 'error' | 'warning',
    alertIcon: React.ReactNode,
    getSuffix: (card: CardWithProject) => { text: string; color: string },
  ) => {
    if (totalCount === 0) return null;
    const projectNames = [...grouped.keys()];
    return (
      <Alert
        message={`${alertMessage} (${totalCount}건)`}
        type={alertType}
        showIcon
        icon={alertIcon}
        style={{ marginBottom: 16 }}
        description={
          <Collapse
            ghost
            defaultActiveKey={projectNames}
            expandIcon={({ isActive }) => <RightOutlined rotate={isActive ? 90 : 0} style={{ fontSize: 10 }} />}
            items={projectNames.map((projectName) => {
              const cards = grouped.get(projectName)!;
              return {
                key: projectName,
                label: (
                  <Text strong style={{ fontSize: 13 }}>
                    {projectName} ({cards.length})
                  </Text>
                ),
                children: (
                  <List
                    size="small"
                    dataSource={cards}
                    renderItem={(card) => {
                      const { text, color } = getSuffix(card);
                      return renderCardItem(card, text, color);
                    }}
                  />
                ),
                style: { padding: 0 },
              };
            })}
          />
        }
      />
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>Dashboard</Title>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="My Projects"
              value={overview?.total_projects || 0}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Projects"
              value={overview?.total_active_projects || 0}
              prefix={<CheckSquareOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="My Cards"
              value={overview?.my_cards_count || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {renderGroupedAlert(
        overdueGrouped,
        overdueCards.length,
        '기한이 초과된 업무',
        'error',
        <WarningOutlined />,
        (card) => {
          const daysOverdue = today.diff(dayjs(card.due_date), 'day');
          return { text: `${daysOverdue}일 초과`, color: '#f5222d' };
        },
      )}

      {renderGroupedAlert(
        approachingGrouped,
        approachingCards.length,
        '마감 임박 업무',
        'warning',
        <ClockCircleOutlined />,
        (card) => {
          const daysLeft = dayjs(card.due_date).diff(today, 'day');
          return {
            text: daysLeft === 0 ? '오늘 마감' : `${daysLeft}일 남음`,
            color: '#faad14',
          };
        },
      )}

      <Title level={4}>My Projects</Title>
      {overview && overview.projects.length > 0 ? (
        <Row gutter={[16, 16]}>
          {overview.projects.map((project) => (
            <Col span={8} key={project.id}>
              <Card
                hoverable
                onClick={() => navigate(`/projects/${project.id}/board`)}
                size="small"
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <ProjectOutlined style={{ color: '#1890ff' }} />
                    <Text strong>{project.name}</Text>
                  </Space>
                  <Space>
                    <Tag>{project.prefix}</Tag>
                    <Tag color={project.status === 'active' ? 'green' : 'default'}>
                      {project.status}
                    </Tag>
                    {project.my_role && (
                      <Tag color="blue">{project.my_role}</Tag>
                    )}
                  </Space>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Empty description="No projects yet." />
      )}
    </div>
  );
};

export default DashboardPage;
