import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Row, Col, Card, Statistic, Tag, Space, Spin, Empty, Alert, List,
} from 'antd';
import {
  ProjectOutlined, CheckSquareOutlined, FileTextOutlined, WarningOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getDashboardOverview, getMyCards } from '@/api/dashboard';
import type { CardWithProject } from '@/api/dashboard';
import { getCardTypeColor, getCardTypeIcon, getCardTypeLabel } from '@/constants/cardTypes';

const { Title, Text } = Typography;

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
  const today = dayjs();

  // 기한 초과 카드
  const overdueCards = myCards.filter(
    (card) => card.due_date && dayjs(card.due_date).isBefore(today, 'day') && !card.completed_at,
  );

  // 마감 임박 카드 (전체 기간 대비 20% 이하 남음)
  const approachingCards = myCards.filter((card) => {
    if (!card.due_date || card.completed_at) return false;
    const dueDate = dayjs(card.due_date);
    const remaining = dueDate.diff(today, 'day');
    if (remaining <= 0) return false; // 이미 초과는 제외
    const startDate = card.start_date || card.created_at;
    const total = dueDate.diff(dayjs(startDate), 'day');
    if (total <= 0) return false;
    return (remaining / total) <= 0.2;
  });

  if (overviewLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const renderCardItem = (card: CardWithProject, suffix: string) => {
    const TypeIcon = getCardTypeIcon(card.card_type);
    return (
      <List.Item style={{ padding: '6px 0' }}>
        <Space>
          <Tag
            color={getCardTypeColor(card.card_type)}
            style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}
          >
            <TypeIcon style={{ fontSize: 10, marginRight: 2 }} />
            {getCardTypeLabel(card.card_type)}
          </Tag>
          <Text type="secondary" style={{ fontSize: 12 }}>[{card.project_name}]</Text>
          <Text style={{ fontSize: 13 }}>{card.title}</Text>
          <Text type="danger" style={{ fontSize: 12 }}>{suffix}</Text>
        </Space>
      </List.Item>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>Dashboard</Title>
      </div>

      {/* Stats */}
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

      {/* 기한 초과 경고 */}
      {overdueCards.length > 0 && (
        <Alert
          message={`기한이 초과된 업무 (${overdueCards.length}건)`}
          type="error"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
          description={
            <List
              size="small"
              dataSource={overdueCards}
              renderItem={(card) => {
                const daysOverdue = today.diff(dayjs(card.due_date), 'day');
                return renderCardItem(card, `${daysOverdue}일 초과`);
              }}
            />
          }
        />
      )}

      {/* 마감 임박 경고 */}
      {approachingCards.length > 0 && (
        <Alert
          message={`마감 임박 업무 (${approachingCards.length}건)`}
          type="warning"
          showIcon
          icon={<ClockCircleOutlined />}
          style={{ marginBottom: 16 }}
          description={
            <List
              size="small"
              dataSource={approachingCards}
              renderItem={(card) => {
                const daysLeft = dayjs(card.due_date).diff(today, 'day');
                return renderCardItem(card, `${daysLeft}일 남음`);
              }}
            />
          }
        />
      )}

      {/* My Projects */}
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
