import React, { useState, useMemo } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Dropdown,
  Avatar,
  Typography,
  Space,
} from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useAuth } from '@/contexts/AuthContext';
import { useRecentProjects } from '@/hooks/useProjects';
import SearchBar from '@/components/common/SearchBar';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { data: recentProjects } = useRecentProjects();

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key.startsWith('/')) {
      navigate(key);
    }
  };

  const menuItems = useMemo((): MenuProps['items'] => {
    const items: MenuProps['items'] = [
      {
        key: '/dashboard',
        icon: <DashboardOutlined />,
        label: 'Dashboard',
      },
    ];

    if (recentProjects && recentProjects.length > 0) {
      const projectItems = recentProjects.map((project) => ({
        key: `/projects/${project.id}/board`,
        label: project.name,
      }));

      items!.push({
        key: 'recent-projects',
        icon: <ProjectOutlined />,
        label: 'Recent Projects',
        children: projectItems,
      } as NonNullable<MenuProps['items']>[number]);
    }

    if (user?.is_superadmin) {
      items!.push({
        key: '/admin',
        icon: <SettingOutlined />,
        label: 'System Admin',
      });
    }

    return items;
  }, [recentProjects, user]);

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.display_name || user?.username || 'Profile',
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
    },
  ];

  const handleUserMenuClick: MenuProps['onClick'] = async ({ key }) => {
    if (key === 'logout') {
      await logout();
      navigate('/login');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={240}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '8px 0',
          }}
        >
          <Text
            strong
            style={{ color: '#fff', fontSize: collapsed ? 16 : 20, letterSpacing: 1 }}
          >
            {collapsed ? 'PS' : 'Planship'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={['recent-projects']}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Space>
            <div style={{ cursor: 'pointer', fontSize: 18 }} onClick={() => setCollapsed(!collapsed)}>
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </div>
            <SearchBar />
          </Space>
          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="bottomRight"
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.display_name || user?.username}</Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
