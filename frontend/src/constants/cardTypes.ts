import React from 'react';
import {
  CrownOutlined,
  BookOutlined,
  CheckSquareOutlined,
  MinusSquareOutlined,
} from '@ant-design/icons';

export interface CardTypeDuration {
  unit: 'month' | 'week' | 'day';
  amount: number;
}

export interface CardTypeConfig {
  color: string;
  icon: React.ComponentType<{ style?: React.CSSProperties }>;
  label: string;
  allowedParents: string[];
  canBeIndependent: boolean;
  displayOrder: number;
}

// 카드가 가질 수 있는 최대 상위 카드 수 (주 부모 + 보조 연결 합계, backend settings.yaml card.max_parents와 동일)
export const MAX_CARD_PARENTS = 5;

// 카드 생성 시 종료일 기본 기간 (backend settings.yaml card.types.*.default_duration의 폴백)
export const DEFAULT_CARD_DURATIONS: Record<string, CardTypeDuration> = {
  epic: { unit: 'month', amount: 3 },
  story: { unit: 'month', amount: 1 },
  task: { unit: 'week', amount: 2 },
  sub_task: { unit: 'week', amount: 1 },
};

export const CARD_TYPE_CONFIG: Record<string, CardTypeConfig> = {
  epic: {
    color: '#722ed1',
    icon: CrownOutlined,
    label: 'Epic',
    allowedParents: [],
    canBeIndependent: true,
    displayOrder: 0,
  },
  story: {
    color: '#1890ff',
    icon: BookOutlined,
    label: 'Story',
    allowedParents: ['epic'],
    canBeIndependent: false,
    displayOrder: 1,
  },
  task: {
    color: '#52c41a',
    icon: CheckSquareOutlined,
    label: 'Task',
    allowedParents: ['epic', 'story'],
    canBeIndependent: true,
    displayOrder: 2,
  },
  sub_task: {
    color: '#faad14',
    icon: MinusSquareOutlined,
    label: 'Sub-task',
    allowedParents: ['task'],
    canBeIndependent: false,
    displayOrder: 3,
  },
};

export function getCardTypeColor(type: string): string {
  return CARD_TYPE_CONFIG[type]?.color ?? '#d9d9d9';
}

export function getCardTypeIcon(type: string): React.ComponentType<{ style?: React.CSSProperties }> {
  return CARD_TYPE_CONFIG[type]?.icon ?? CheckSquareOutlined;
}

export function getCardTypeLabel(type: string): string {
  return CARD_TYPE_CONFIG[type]?.label ?? type;
}

export const CARD_TYPE_SORT_ORDER: Record<string, number> = Object.fromEntries(
  Object.entries(CARD_TYPE_CONFIG).map(([key, config]) => [key, config.displayOrder])
);

export function getAllowedChildTypes(parentType: string): string[] {
  return Object.entries(CARD_TYPE_CONFIG)
    .filter(([, config]) => config.allowedParents.includes(parentType))
    .sort(([, a], [, b]) => a.displayOrder - b.displayOrder)
    .map(([key]) => key);
}
