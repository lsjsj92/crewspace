import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Row,
  Col,
  Card,
  Statistic,
  Tag,
  Space,
  Spin,
  Empty,
} from 'antd';
import {
  ProjectOutlined,
  CheckSquareOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useMyProjects } from '@/hooks/useProjects';
import type { Project } from '@/types';

const { Title, Text } = Typography;

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useMyProjects();

  const totalProjects = projects?.length || 0;
  const activeProjects = projects?.filter((p) => p.status === 'active').length || 0;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          Dashboard
        </Title>
      </div>

      {/* Stats */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="My Projects"
              value={totalProjects}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Active Projects"
              value={activeProjects}
              prefix={<CheckSquareOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="My Cards"
              value={0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Projects */}
      <Title level={4}>My Projects</Title>
      {projects && projects.length > 0 ? (
        <Row gutter={[16, 16]}>
          {projects.map((project: Project) => (
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
                  </Space>
                  {project.description && (
                    <Text type="secondary" ellipsis>
                      {project.description}
                    </Text>
                  )}
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
