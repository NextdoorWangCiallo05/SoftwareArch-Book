/** 与后端枚举（app/domain/value_objects/enums.py）保持一致的展示字典。 */

export const READER_TYPES = [
  { value: 'ASSOCIATE', label: '专科生' },
  { value: 'UNDERGRADUATE', label: '本科生' },
  { value: 'GRADUATE', label: '研究生' },
  { value: 'DOCTOR', label: '博士生' },
  { value: 'TEACHER', label: '教师' },
]

export const ITEM_TYPES = [
  { value: 'BOOK', label: '图书' },
  { value: 'MAGAZINE', label: '期刊' },
  { value: 'THESIS', label: '学位论文' },
]

export const FINE_CATEGORIES = [
  { value: 'CHINESE_BOOK', label: '中文图书' },
  { value: 'FOREIGN_BOOK', label: '外文图书' },
  { value: 'CHINESE_MAGAZINE', label: '中文期刊' },
  { value: 'FOREIGN_MAGAZINE', label: '外文期刊' },
]

export const ITEM_STATUS = {
  AVAILABLE: { label: '在馆', tone: 'success' },
  BORROWED: { label: '已借出', tone: 'warning' },
  RESERVED: { label: '已预约', tone: 'primary' },
  REMOVED: { label: '已下架', tone: 'neutral' },
}

export const LOAN_STATUS = {
  BORROWED: { label: '借阅中', tone: 'primary' },
  RETURN_REQUESTED: { label: '待审核归还', tone: 'warning' },
  RETURNED: { label: '已归还', tone: 'success' },
  OVERDUE: { label: '已逾期', tone: 'danger' },
}

export const RESERVATION_STATUS = {
  ACTIVE: { label: '排队中', tone: 'primary' },
  CANCELLED: { label: '已取消', tone: 'neutral' },
  FULFILLED: { label: '已满足', tone: 'success' },
  EXPIRED: { label: '已过期', tone: 'warning' },
}

export const READER_STATUS = {
  active: { label: '正常', tone: 'success' },
  inactive: { label: '已停用', tone: 'danger' },
}

export const CARD_STATUS = {
  ACTIVE: { label: '有效', tone: 'success' },
  LOST: { label: '已挂失', tone: 'warning' },
  REVOKED: { label: '已注销', tone: 'neutral' },
}

export const ROLE_LABELS = {
  reader: '读者',
  librarian: '图书管理员',
  admin: '系统管理员',
}

export function labelOf(dict, key, fallback = '-') {
  const hit = dict[key]
  if (!hit) return fallback
  return typeof hit === 'string' ? hit : hit.label
}

export function toneOf(dict, key) {
  return dict[key]?.tone || 'neutral'
}

export function readerTypeLabel(value) {
  return READER_TYPES.find((t) => t.value === value)?.label || value || '-'
}

export function itemTypeLabel(value) {
  return ITEM_TYPES.find((t) => t.value === value)?.label || value || '-'
}

export function fineCategoryLabel(value) {
  return FINE_CATEGORIES.find((c) => c.value === value)?.label || value || '-'
}

/** 金额格式化：后端以 Decimal 传出，可能为字符串。 */
export function money(value) {
  const num = Number(value ?? 0)
  return Number.isFinite(num) ? num.toFixed(2) : '0.00'
}
