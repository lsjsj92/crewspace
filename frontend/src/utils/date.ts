import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD');
}

// KST(UTC+9) 기준 오늘 날짜를 로컬 dayjs 객체(date-only)로 반환한다.
export function todayKst(): dayjs.Dayjs {
  return dayjs(dayjs().utc().add(9, 'hour').format('YYYY-MM-DD'));
}

// 기준일에 카드 타입별 기본 기간을 더한다 (unit: month | week | day).
export function addDuration(
  base: dayjs.Dayjs,
  duration: { unit: 'month' | 'week' | 'day'; amount: number }
): dayjs.Dayjs {
  return base.add(duration.amount, duration.unit);
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
}

export function isOverdue(date: string | Date | null | undefined): boolean {
  if (!date) return false;
  return dayjs(date).isBefore(dayjs(), 'day');
}
