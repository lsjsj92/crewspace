import React, { useState, useEffect, useMemo } from 'react';
import {
  Drawer,
  Typography,
  Input,
  Select,
  DatePicker,
  Tag,
  Avatar,
  Button,
  List,
  Space,
  Divider,
  Popconfirm,
  message,
} from 'antd';
import {
  DeleteOutlined,
  PlusOutlined,
  UserAddOutlined,
  SendOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import type { Card, ProjectMember, Label, CardPriority } from '@/types';
import {
  getCard,
  getProjectCards,
  updateCard,
  deleteCard,
  addAssignee,
  removeAssignee,
  addLabel,
  removeLabel,
  getCardChildren,
} from '@/api/cards';
import { getComments, createComment, deleteComment } from '@/api/comments';
import { getLabels } from '@/api/labels';
import { getProjectMembers } from '@/api/projects';
import { getCardTypeColor, getCardTypeIcon, getCardTypeLabel, CARD_TYPE_CONFIG } from '@/constants/cardTypes';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const PRIORITY_OPTIONS = [
  { value: 'lowest', label: 'Lowest' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'highest', label: 'Highest' },
];

interface CardDetailDrawerProps {
  cardId: string | null;
  projectId: string;
  teamId?: string;
  prefix: string;
  columnName?: string;
  open: boolean;
  onClose: () => void;
  onCreateSubCard?: (parentId: string, columnId: string, parentType?: string) => void;
  onNavigateCard?: (cardId: string) => void;
}

const CardDetailDrawer: React.FC<CardDetailDrawerProps> = ({
  cardId,
  projectId,
  prefix,
  columnName,
  open,
  onClose,
  onCreateSubCard,
  onNavigateCard,
}) => {
  const queryClient = useQueryClient();
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState('');
  const [descValue, setDescValue] = useState('');
  const [editingDesc, setEditingDesc] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [linkChildOpen, setLinkChildOpen] = useState(false);
  const [linkParentOpen, setLinkParentOpen] = useState(false);

  const { data: card, isLoading: cardLoading } = useQuery<Card>({
    queryKey: ['card', cardId],
    queryFn: () => getCard(cardId!),
    enabled: !!cardId && open,
  });

  const { data: comments } = useQuery({
    queryKey: ['comments', cardId],
    queryFn: () => getComments(cardId!),
    enabled: !!cardId && open,
  });

  const { data: children } = useQuery({
    queryKey: ['card-children', cardId],
    queryFn: () => getCardChildren(cardId!),
    enabled: !!cardId && open && (card?.card_type === 'epic' || card?.card_type === 'story' || card?.card_type === 'task'),
  });

  const { data: labels } = useQuery<Label[]>({
    queryKey: ['labels', projectId],
    queryFn: () => getLabels(projectId),
    enabled: open,
  });

  const { data: members } = useQuery<ProjectMember[]>({
    queryKey: ['project-members', projectId],
    queryFn: () => getProjectMembers(projectId),
    enabled: open && !!projectId,
  });

  useEffect(() => {
    if (card) {
      setTitleValue(card.title);
      setDescValue(card.description || '');
    }
  }, [card]);

  // Board 및 Timeline 데이터를 모두 갱신
  const invalidateBoard = () => {
    queryClient.invalidateQueries({ queryKey: ['board', projectId] });
    queryClient.invalidateQueries({ queryKey: ['project-cards', projectId] });
  };

  // 기존 카드를 하위 카드로 연결하기 위한 프로젝트 카드 조회
  const { data: projectCards } = useQuery<Card[]>({
    queryKey: ['project-cards', projectId],
    queryFn: () => getProjectCards(projectId),
    enabled: open && (linkChildOpen || linkParentOpen),
  });

  // 하위 카드로 연결 가능한 카드 필터링
  const validLinkableCards = useMemo(() => {
    if (!projectCards || !card) return [];
    const cardType = card.card_type;
    return projectCards.filter((c) => {
      if (c.id === card.id) return false;
      if (c.parent_id) return false;
      const childConfig = CARD_TYPE_CONFIG[c.card_type];
      return childConfig?.allowedParents?.includes(cardType);
    });
  }, [projectCards, card]);

  // 상위 카드로 연결 가능한 카드 필터링
  const validParentCards = useMemo(() => {
    if (!projectCards || !card) return [];
    const allowedParents = CARD_TYPE_CONFIG[card.card_type]?.allowedParents || [];
    if (allowedParents.length === 0) return [];
    return projectCards.filter((c) => {
      if (c.id === card.id) return false;
      if (c.id === card.parent_id) return false;
      return allowedParents.includes(c.card_type);
    });
  }, [projectCards, card]);

  // 기존 카드를 하위 카드로 연결
  const linkChildMutation = useMutation({
    mutationFn: (childCardId: string) => updateCard(childCardId, { parent_id: card!.id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card-children', cardId] });
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
      setLinkChildOpen(false);
      message.success('Card linked');
    },
    onError: () => {
      message.error('Failed to link card');
    },
  });

  // 상위 카드 연결
  const linkParentMutation = useMutation({
    mutationFn: (parentCardId: string) => updateCard(cardId!, { parent_id: parentCardId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      queryClient.invalidateQueries({ queryKey: ['card-children'] });
      invalidateBoard();
      setLinkParentOpen(false);
      message.success('상위 카드가 연결되었습니다');
    },
    onError: () => {
      message.error('상위 카드 연결에 실패했습니다');
    },
  });

  // 상위 카드 연결 해제
  const unlinkParentMutation = useMutation({
    mutationFn: () => updateCard(cardId!, { parent_id: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      queryClient.invalidateQueries({ queryKey: ['card-children'] });
      invalidateBoard();
      message.success('상위 카드 연결이 해제되었습니다');
    },
    onError: () => {
      message.error('연결 해제에 실패했습니다');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => updateCard(cardId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteCard(cardId!),
    onSuccess: () => {
      invalidateBoard();
      onClose();
      message.success('Card deleted');
    },
  });

  const addAssigneeMutation = useMutation({
    mutationFn: (userId: string) => addAssignee(cardId!, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
    },
  });

  const removeAssigneeMutation = useMutation({
    mutationFn: (userId: string) => removeAssignee(cardId!, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
    },
  });

  const addLabelMutation = useMutation({
    mutationFn: (labelId: string) => addLabel(cardId!, labelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
    },
  });

  const removeLabelMutation = useMutation({
    mutationFn: (labelId: string) => removeLabel(cardId!, labelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['card', cardId] });
      invalidateBoard();
    },
  });

  const addCommentMutation = useMutation({
    mutationFn: (content: string) => createComment(cardId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', cardId] });
      setCommentText('');
    },
  });

  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: string) => deleteComment(commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', cardId] });
    },
  });

  const handleTitleSave = () => {
    if (titleValue.trim() && titleValue !== card?.title) {
      updateMutation.mutate({ title: titleValue.trim() });
    }
    setEditingTitle(false);
  };

  const handleDescSave = () => {
    if (descValue !== (card?.description || '')) {
      updateMutation.mutate({ description: descValue });
    }
    setEditingDesc(false);
  };

  const handlePriorityChange = (value: CardPriority) => {
    updateMutation.mutate({ priority: value });
  };

  const handleDateChange = (field: 'start_date' | 'due_date', date: dayjs.Dayjs | null) => {
    updateMutation.mutate({ [field]: date ? date.format('YYYY-MM-DD') : null });
  };

  const handleAddComment = () => {
    if (commentText.trim()) {
      addCommentMutation.mutate(commentText.trim());
    }
  };

  const existingAssigneeIds = card?.assignees?.map((a) => a.user_id) || [];
  const existingLabelIds = card?.labels?.map((l) => l.label_id) || [];
  const availableMembers = members?.filter((m) => !existingAssigneeIds.includes(m.user_id)) || [];
  const availableLabels = labels?.filter((l) => !existingLabelIds.includes(l.id)) || [];

  if (!cardId) return null;

  return (
    <Drawer
      title={null}
      open={open}
      onClose={onClose}
      width={600}
      loading={cardLoading}
    >
      {card && (
        <div>
          <Space style={{ marginBottom: 8 }}>
            <Tag color={getCardTypeColor(card.card_type)}>
              {React.createElement(getCardTypeIcon(card.card_type), { style: { marginRight: 4, fontSize: 12 } })}
              {getCardTypeLabel(card.card_type)}
            </Tag>
            <Text type="secondary">{prefix}-{card.card_number}</Text>
            {columnName && <Tag>{columnName}</Tag>}
          </Space>

          {editingTitle ? (
            <Input
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={handleTitleSave}
              onPressEnter={handleTitleSave}
              autoFocus
              style={{ marginBottom: 16 }}
            />
          ) : (
            <Title
              level={4}
              style={{ cursor: 'pointer', marginBottom: 16 }}
              onClick={() => setEditingTitle(true)}
            >
              {card.title}
            </Title>
          )}

          <Text strong>Description</Text>
          {editingDesc ? (
            <div style={{ marginTop: 4 }}>
              <TextArea
                value={descValue}
                onChange={(e) => setDescValue(e.target.value)}
                rows={4}
                autoFocus
              />
              <Space style={{ marginTop: 4 }}>
                <Button size="small" type="primary" onClick={handleDescSave}>Save</Button>
                <Button size="small" onClick={() => setEditingDesc(false)}>Cancel</Button>
              </Space>
            </div>
          ) : (
            <Paragraph
              style={{
                cursor: 'pointer',
                padding: 8,
                background: '#fafafa',
                borderRadius: 4,
                minHeight: 60,
                marginTop: 4,
              }}
              onClick={() => setEditingDesc(true)}
            >
              {card.description || 'Click to add description...'}
            </Paragraph>
          )}

          <Divider />

          <div style={{ marginBottom: 16 }}>
            <Text strong>Priority</Text>
            <br />
            <Select
              value={card.priority}
              onChange={handlePriorityChange}
              options={PRIORITY_OPTIONS}
              style={{ width: 200, marginTop: 4 }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <Space size={16}>
              <div>
                <Text strong>Start Date</Text>
                <br />
                <DatePicker
                  value={card.start_date ? dayjs(card.start_date) : null}
                  onChange={(date) => handleDateChange('start_date', date)}
                  style={{ marginTop: 4 }}
                />
              </div>
              <div>
                <Text strong>Due Date</Text>
                <br />
                <DatePicker
                  value={card.due_date ? dayjs(card.due_date) : null}
                  onChange={(date) => handleDateChange('due_date', date)}
                  style={{ marginTop: 4 }}
                />
              </div>
            </Space>
          </div>

          <Divider />

          <div style={{ marginBottom: 16 }}>
            <Text strong>Assignees</Text>
            <div style={{ marginTop: 8 }}>
              {card.assignees?.map((a) => (
                <Tag
                  key={a.id}
                  closable
                  onClose={() => removeAssigneeMutation.mutate(a.user_id)}
                  style={{ marginBottom: 4 }}
                >
                  <Avatar size="small" style={{ marginRight: 4, backgroundColor: '#1890ff' }}>
                    {(a.user?.display_name || a.user?.username || '?')[0].toUpperCase()}
                  </Avatar>
                  {a.user?.display_name || a.user?.username}
                </Tag>
              ))}
              {availableMembers.length > 0 && (
                <Select
                  placeholder="Add assignee"
                  style={{ width: 200 }}
                  size="small"
                  suffixIcon={<UserAddOutlined />}
                  value={undefined}
                  onChange={(userId: string) => addAssigneeMutation.mutate(userId)}
                  options={availableMembers.map((m) => ({
                    value: m.user_id,
                    label: m.user?.display_name || m.user?.username || `User ${m.user_id}`,
                  }))}
                />
              )}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <Text strong>Labels</Text>
            <div style={{ marginTop: 8 }}>
              {card.labels?.map((cl) =>
                cl.label ? (
                  <Tag
                    key={cl.label_id}
                    color={cl.label.color}
                    closable
                    onClose={() => removeLabelMutation.mutate(cl.label_id)}
                    style={{ marginBottom: 4 }}
                  >
                    {cl.label.name}
                  </Tag>
                ) : null
              )}
              {availableLabels.length > 0 && (
                <Select
                  placeholder="Add label"
                  style={{ width: 200 }}
                  size="small"
                  suffixIcon={<PlusOutlined />}
                  value={undefined}
                  onChange={(labelId: string) => addLabelMutation.mutate(labelId)}
                  options={availableLabels.map((l) => ({
                    value: l.id,
                    label: l.name,
                  }))}
                />
              )}
            </div>
          </div>

          <Divider />

          {/* Parent Card 섹션 */}
          {card.card_type !== 'epic' && (
            <>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text strong>상위 카드</Text>
                  {!card.parent && CARD_TYPE_CONFIG[card.card_type]?.allowedParents?.length > 0 && (
                    <Button
                      size="small"
                      icon={<LinkOutlined />}
                      onClick={() => setLinkParentOpen(!linkParentOpen)}
                    >
                      상위 카드 연결
                    </Button>
                  )}
                </div>
                {card.parent ? (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: '#fafafa',
                      borderRadius: 4,
                      borderLeft: `3px solid ${getCardTypeColor(card.parent.card_type)}`,
                      cursor: 'pointer',
                    }}
                    onClick={() => onNavigateCard?.(card.parent!.id)}
                  >
                    <Space>
                      <Tag
                        color={getCardTypeColor(card.parent.card_type)}
                        style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px', margin: 0 }}
                      >
                        {React.createElement(getCardTypeIcon(card.parent.card_type), { style: { marginRight: 2, fontSize: 10 } })}
                        {getCardTypeLabel(card.parent.card_type)}
                      </Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>{prefix}-{card.parent.card_number}</Text>
                      <Text style={{ fontSize: 13 }}>{card.parent.title}</Text>
                    </Space>
                    {CARD_TYPE_CONFIG[card.card_type]?.canBeIndependent && (
                      <Popconfirm
                        title="상위 카드 연결을 해제하시겠습니까?"
                        onConfirm={() => unlinkParentMutation.mutate()}
                      >
                        <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                      </Popconfirm>
                    )}
                  </div>
                ) : (
                  <>
                    {linkParentOpen && (
                      <Select
                        showSearch
                        placeholder="상위 카드 검색..."
                        style={{ width: '100%', marginBottom: 8 }}
                        optionFilterProp="label"
                        value={undefined}
                        onChange={(parentCardId: string) => linkParentMutation.mutate(parentCardId)}
                        loading={!projectCards}
                        options={validParentCards.map((c) => ({
                          value: c.id,
                          label: `${prefix}-${c.card_number}: ${c.title}`,
                        }))}
                        notFoundContent="연결 가능한 상위 카드가 없습니다"
                      />
                    )}
                    {!linkParentOpen && <Text type="secondary">상위 카드 없음</Text>}
                  </>
                )}
              </div>
              <Divider />
            </>
          )}

          {(card.card_type === 'epic' || card.card_type === 'story' || card.card_type === 'task') && (
            <>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text strong>Sub-cards</Text>
                  <Space size={4}>
                    <Button
                      size="small"
                      icon={<LinkOutlined />}
                      onClick={() => setLinkChildOpen(!linkChildOpen)}
                    >
                      Link card
                    </Button>
                    {onCreateSubCard && (
                      <Button
                        size="small"
                        icon={<PlusOutlined />}
                        onClick={() => onCreateSubCard(card.id, card.column_id, card.card_type)}
                      >
                        Create sub-card
                      </Button>
                    )}
                  </Space>
                </div>
                {linkChildOpen && (
                  <Select
                    showSearch
                    placeholder="Search cards to link..."
                    style={{ width: '100%', marginBottom: 8 }}
                    optionFilterProp="label"
                    value={undefined}
                    onChange={(childCardId: string) => linkChildMutation.mutate(childCardId)}
                    loading={!projectCards}
                    options={validLinkableCards.map((c) => ({
                      value: c.id,
                      label: `${prefix}-${c.card_number}: ${c.title}`,
                    }))}
                    notFoundContent="No linkable cards"
                  />
                )}
                {children && children.length > 0 ? (
                  <List
                    size="small"
                    dataSource={children}
                    renderItem={(child: Card) => (
                      <List.Item>
                        <Space>
                          <Tag color={getCardTypeColor(child.card_type)} style={{ fontSize: 10 }}>
                            {React.createElement(getCardTypeIcon(child.card_type), { style: { marginRight: 2, fontSize: 10 } })}
                            {getCardTypeLabel(child.card_type)}
                          </Tag>
                          <Text>{prefix}-{child.card_number}</Text>
                          <Text>{child.title}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Text type="secondary">No sub-cards</Text>
                )}
              </div>
              <Divider />
            </>
          )}

          <div style={{ marginBottom: 16 }}>
            <Text strong>Comments</Text>
            <div style={{ marginTop: 8 }}>
              <TextArea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Write a comment..."
                rows={2}
              />
              <Button
                type="primary"
                size="small"
                icon={<SendOutlined />}
                onClick={handleAddComment}
                loading={addCommentMutation.isPending}
                disabled={!commentText.trim()}
                style={{ marginTop: 4 }}
              >
                Comment
              </Button>
            </div>
            {comments && comments.length > 0 && (
              <List
                style={{ marginTop: 16 }}
                dataSource={comments}
                renderItem={(comment) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        key="delete"
                        title="Delete comment?"
                        onConfirm={() => deleteCommentMutation.mutate(comment.id)}
                      >
                        <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar size="small" style={{ backgroundColor: '#1890ff' }}>
                          {(comment.user?.display_name || comment.user?.username || '?')[0].toUpperCase()}
                        </Avatar>
                      }
                      title={
                        <Space>
                          <Text strong style={{ fontSize: 12 }}>
                            {comment.user?.display_name || comment.user?.username}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {dayjs(comment.created_at).format('YYYY-MM-DD HH:mm')}
                          </Text>
                        </Space>
                      }
                      description={comment.content}
                    />
                  </List.Item>
                )}
              />
            )}
          </div>

          <Divider />

          <Popconfirm
            title="Delete this card?"
            description="This action cannot be undone."
            onConfirm={() => deleteMutation.mutate()}
          >
            <Button danger icon={<DeleteOutlined />}>Delete Card</Button>
          </Popconfirm>
        </div>
      )}
    </Drawer>
  );
};

export default CardDetailDrawer;
