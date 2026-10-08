import { createRouter, createWebHistory } from 'vue-router'

import { homeRoute, useAuth } from '../composables/useAuth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, blank: true, title: '登录' },
  },
  { path: '/', redirect: '/search' },

  // ---- 读者端 ----
  {
    path: '/search',
    name: 'search',
    component: () => import('../views/reader/SearchView.vue'),
    meta: { title: '图书检索' },
  },
  {
    path: '/book/:titleId',
    name: 'book-detail',
    component: () => import('../views/reader/BookDetailView.vue'),
    meta: { title: '图书详情' },
  },
  {
    path: '/my/loans',
    name: 'my-loans',
    component: () => import('../views/reader/MyLoansView.vue'),
    meta: { title: '我的借阅记录', roles: ['reader'] },
  },
  {
    path: '/my/reservations',
    name: 'my-reservations',
    component: () => import('../views/reader/MyReservationsView.vue'),
    meta: { title: '我的预约', roles: ['reader'] },
  },

  // ---- 馆员端（BR-011：流通办理仅图书管理员） ----
  {
    path: '/circ/borrow',
    name: 'circ-borrow',
    component: () => import('../views/staff/BorrowView.vue'),
    meta: { title: '借书办理', roles: ['librarian'] },
  },
  {
    path: '/circ/return',
    name: 'circ-return',
    component: () => import('../views/staff/ReturnView.vue'),
    meta: { title: '还书办理', roles: ['librarian'] },
  },
  {
    path: '/circ/return-audit',
    name: 'circ-return-audit',
    component: () => import('../views/staff/ReturnAuditView.vue'),
    meta: { title: '还书审核', roles: ['librarian'] },
  },
  {
    path: '/circ/charges',
    name: 'circ-charges',
    component: () => import('../views/staff/ChargesView.vue'),
    meta: { title: '罚款与赔偿', roles: ['librarian'] },
  },
  {
    path: '/circ/reader-records',
    name: 'circ-records',
    component: () => import('../views/staff/ReaderRecordsView.vue'),
    meta: { title: '读者借阅查询', roles: ['librarian'] },
  },

  // ---- 管理端 ----
  {
    path: '/admin/readers',
    name: 'admin-readers',
    component: () => import('../views/admin/ReadersView.vue'),
    meta: { title: '读者与借阅证', roles: ['admin'] },
  },
  {
    path: '/admin/catalog',
    name: 'admin-catalog',
    component: () => import('../views/admin/CatalogView.vue'),
    meta: { title: '馆藏维护', roles: ['admin'] },
  },
  {
    path: '/admin/policies',
    name: 'admin-policies',
    component: () => import('../views/admin/PoliciesView.vue'),
    meta: { title: '借阅与罚款规则', roles: ['admin'] },
  },
  {
    path: '/admin/reviews',
    name: 'admin-reviews',
    component: () => import('../views/admin/ReviewsView.vue'),
    meta: { title: '评论审核', roles: ['admin'] },
  },
  {
    path: '/admin/librarians',
    name: 'admin-librarians',
    component: () => import('../views/admin/LibrariansView.vue'),
    meta: { title: '管理员账号', roles: ['admin'] },
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'notfound',
    component: () => import('../views/NotFoundView.vue'),
    meta: { public: true, blank: true, title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.state.ready) await auth.loadProfile()

  if (to.meta.public) {
    if (to.name === 'login' && auth.isLoggedIn.value) return homeRoute(auth.role.value)
    return true
  }

  if (!auth.isLoggedIn.value) {
    return { name: 'login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : {} }
  }

  const allowed = to.meta.roles
  if (allowed && !allowed.includes(auth.role.value)) {
    return homeRoute(auth.role.value)
  }

  return true
})

export default router
