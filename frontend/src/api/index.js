/**
 * 后端接口封装。路径与 backend/app/presentation/routers 一一对应，
 * 参数名严格对齐 Pydantic 请求 DTO，避免字段名漂移。
 */
import { http } from './http'

export const authApi = {
  register: (payload) => http.post('/api/auth/register', payload, { auth: false }),
  login: (payload) => http.post('/api/auth/login', payload, { auth: false }),
  me: () => http.get('/api/auth/me'),
  logout: () => http.post('/api/auth/logout'),
}

export const catalogApi = {
  // 参数：keyword / author / category / item_type / page / page_size
  search: (params) => http.get('/api/books/search', { params }),
  detail: (titleId) => http.get(`/api/books/${titleId}`),
}

export const circulationApi = {
  borrow: (payload) => http.post('/api/circulation/borrow', payload),
  returnBook: (payload) => http.post('/api/circulation/return', payload),
  // BR-020：读者发起归还申请 + 图书管理员审核
  requestReturn: (loanId) => http.post('/api/circulation/return-request', { loan_id: loanId }),
  listReturnRequests: () => http.get('/api/circulation/return-requests'),
  approveReturn: (loanId) => http.post(`/api/circulation/return-requests/${loanId}/approve`),
  rejectReturn: (loanId) => http.post(`/api/circulation/return-requests/${loanId}/reject`),
  renew: (loanId) => http.post('/api/circulation/renew', { loan_id: loanId }),
  records: (readerId, status) =>
    http.get(`/api/circulation/records/${readerId}`, { params: { status } }),
  reportLost: (barcode) => http.post('/api/circulation/lost', { barcode }),
  listFines: (params) => http.get('/api/circulation/fines', { params }),
  payFine: (fineId) => http.post(`/api/circulation/fines/${fineId}/pay`),
  listLosts: (params) => http.get('/api/circulation/lost', { params }),
  payLost: (lostId) => http.post(`/api/circulation/lost/${lostId}/pay`),
}

export const reservationApi = {
  create: (titleId) => http.post('/api/reservations', { title_id: titleId }),
  cancel: (reservationId) => http.post(`/api/reservations/${reservationId}/cancel`),
  list: (readerId) => http.get('/api/reservations', { params: { reader_id: readerId } }),
}

export const reviewApi = {
  submit: (payload) => http.post('/api/reviews', payload),
  listByTitle: (titleId) => http.get('/api/reviews', { params: { title_id: titleId } }),
  listPending: () => http.get('/api/reviews/pending'),
  moderate: (reviewId, decision) =>
    http.post(`/api/reviews/${reviewId}/moderate`, { decision }),
}

export const adminApi = {
  // 读者
  listReaders: (params) => http.get('/api/admin/readers', { params }),
  updateReader: (readerId, payload) => http.put(`/api/admin/readers/${readerId}`, payload),
  deactivateReader: (readerId) => http.post(`/api/admin/readers/${readerId}/deactivate`),
  // 借阅证
  issueCard: (readerId) => http.post('/api/admin/cards', { reader_id: readerId }),
  revokeCard: (cardId) => http.post(`/api/admin/cards/${cardId}/revoke`),
  // 图书管理员账号
  listLibrarians: (params) => http.get('/api/admin/librarians', { params }),
  addLibrarian: (payload) => http.post('/api/admin/librarians', payload),
  updateLibrarian: (librarianId, payload) =>
    http.put(`/api/admin/librarians/${librarianId}`, payload),
  removeLibrarian: (librarianId) => http.del(`/api/admin/librarians/${librarianId}`),
  // 图书与馆藏
  addTitle: (payload) => http.post('/api/admin/titles', payload),
  updateTitle: (titleId, payload) => http.put(`/api/admin/titles/${titleId}`, payload),
  deactivateTitle: (titleId) => http.post(`/api/admin/titles/${titleId}/deactivate`),
  addItems: (payload) => http.post('/api/admin/items', payload),
  removeItem: (itemId) => http.post(`/api/admin/items/${itemId}/remove`),
  // 规则
  listBorrowPolicies: () => http.get('/api/admin/policies/borrow'),
  listFineRules: () => http.get('/api/admin/policies/fine'),
  upsertBorrowPolicy: (payload) => http.put('/api/admin/policies/borrow', payload),
  upsertFineRule: (payload) => http.put('/api/admin/policies/fine', payload),
}

export const systemApi = {
  health: () => http.get('/api/health', { auth: false }),
}
