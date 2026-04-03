// frontend/src/utils/weeklyTemplate.ts
// 주간 일정 템플릿 생성 유틸리티

import type { WeeklyViewResponse, WeeklyCardItem } from '@/api/weekly';

function formatDate(dateStr: string): string {
  return dateStr.replace(/-/g, '.');
}

function padStatus(text: string, status: string, totalWidth: number): string {
  const textLen = text.length;
  const statusLen = status.length;
  const gap = Math.max(totalWidth - textLen - statusLen, 4);
  return text + ' '.repeat(gap) + status;
}

function formatCardLine(item: WeeklyCardItem): string {
  const parts: string[] = [];
  if (item.epic_title) parts.push(item.epic_title);
  if (item.story_title) parts.push(item.story_title);
  parts.push(item.task_title);

  const hierarchy = parts.join(' - ');
  const dueStr = item.due_date ? `(~${formatDate(item.due_date)})` : '';
  const content = `- ${hierarchy}${dueStr}`;

  return padStatus(content, item.status, 60);
}

export function generateWeeklyTemplate(
  data: WeeklyViewResponse,
  format: 'txt' | 'md',
): string {
  const lines: string[] = [];
  const weekStartFmt = formatDate(data.week_start);
  const weekEndFmt = formatDate(data.week_end);
  const bold = (s: string) => (format === 'md' ? `**${s}**` : s);

  // 기준 주간 일자
  lines.push('# 기준 주간 일자');
  lines.push(`- ${weekStartFmt} ~ ${weekEndFmt}`);
  lines.push('');

  // 월간 목표
  lines.push(`# [${data.month}월] 월간 목표`);
  if (data.monthly_goals.length === 0) {
    lines.push('- (없음)');
  } else {
    for (const group of data.monthly_goals) {
      for (const item of group.items) {
        const content = `- [${group.epic_title}] ${item.title}`;
        lines.push(padStatus(content, bold(item.status), 60));
      }
    }
  }
  lines.push('');

  // 진행해야 할 프로젝트
  lines.push('# 진행해야 할 프로젝트');
  if (data.active_projects.length === 0) {
    lines.push('- (없음)');
  } else {
    const seen = new Set<string>();
    for (const proj of data.active_projects) {
      if (!seen.has(proj.epic_title)) {
        seen.add(proj.epic_title);
        lines.push(`- ${proj.epic_title}`);
      }
    }
  }
  lines.push('');

  // 지난 주 목표 및 달성 현황
  lines.push('# 지난 주 목표 및 달성 현황');
  if (data.last_week_items.length === 0) {
    lines.push('- (없음)');
  } else {
    for (const item of data.last_week_items) {
      const line = formatCardLine(item);
      if (format === 'md') {
        lines.push(line.replace(item.status, bold(item.status)));
      } else {
        lines.push(line);
      }
    }
  }
  lines.push('');

  // 주간 목표
  lines.push('# 주간 목표');
  if (data.this_week_items.length === 0) {
    lines.push('- (없음)');
  } else {
    for (const item of data.this_week_items) {
      const line = formatCardLine(item);
      if (format === 'md') {
        lines.push(line.replace(item.status, bold(item.status)));
      } else {
        lines.push(line);
      }
    }
  }
  lines.push('');

  return lines.join('\n');
}

export function downloadWeeklyTemplate(
  data: WeeklyViewResponse,
  format: 'txt' | 'md',
): void {
  const content = generateWeeklyTemplate(data, format);
  const weekStartFmt = formatDate(data.week_start);
  const weekEndFmt = formatDate(data.week_end);
  const fileName = `주간일정_${weekStartFmt}-${weekEndFmt}.${format}`;

  const blob = new Blob(['\uFEFF' + content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
