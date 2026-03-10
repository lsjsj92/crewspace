import dayjs from 'dayjs';

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD');
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '';
  return dayjs(date).format('YYYY-MM-DD HH:mm');
}

export function isOverdue(date: string | Date | null | undefined): boolean {
  if (!date) return false;
  return dayjs(date).isBefore(dayjs(), 'day');
}
