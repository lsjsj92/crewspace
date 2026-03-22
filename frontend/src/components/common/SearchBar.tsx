import React, { useState } from 'react';
import { Input, Modal, List, Tag, Typography, Empty, Spin } from 'antd';
import { ProjectOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { searchAll, type SearchResult } from '@/api/search';
import { getCardTypeColor } from '@/constants/cardTypes';

const { Search } = Input;
const { Text } = Typography;

const SearchBar: React.FC = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');

  const handleSearch = async (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;

    setQuery(trimmed);
    setOpen(true);
    setLoading(true);
    try {
      const data = await searchAll(trimmed);
      setResults(data.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (item: SearchResult) => {
    setOpen(false);
    if (item.type === 'project') {
      navigate(`/projects/${item.id}/board`);
    } else if (item.type === 'card') {
      navigate(`/projects/${item.project_id}/board`);
    }
  };

  return (
    <>
      <Search
        placeholder="Search projects, cards..."
        onSearch={handleSearch}
        style={{ width: 280 }}
        allowClear
      />
      <Modal
        title={`Search results: "${query}"`}
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={600}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 32 }}>
            <Spin />
          </div>
        ) : results.length === 0 ? (
          <Empty description="No results found" />
        ) : (
          <List
            dataSource={results}
            renderItem={(item) => (
              <List.Item
                onClick={() => handleResultClick(item)}
                style={{ cursor: 'pointer' }}
              >
                <List.Item.Meta
                  avatar={
                    item.type === 'project' ? (
                      <ProjectOutlined style={{ fontSize: 20 }} />
                    ) : (
                      <FileTextOutlined style={{ fontSize: 20 }} />
                    )
                  }
                  title={
                    <span>
                      {item.title}{' '}
                      <Tag color={item.type === 'project' ? 'blue' : 'green'}>
                        {item.type === 'project' ? 'Project' : 'Card'}
                      </Tag>
                      {item.type === 'card' && item.card_type && (
                        <Tag color={getCardTypeColor(item.card_type)}>{item.card_type}</Tag>
                      )}
                    </span>
                  }
                  description={
                    <Text type="secondary" ellipsis>
                      {item.description || 'No description'}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Modal>
    </>
  );
};

export default SearchBar;
