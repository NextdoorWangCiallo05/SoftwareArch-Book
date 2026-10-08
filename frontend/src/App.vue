<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { systemApi } from './api'
import ToastHost from './components/ToastHost.vue'
import { ROLE_LABELS } from './constants'
import { useAuth } from './composables/useAuth'
import { useToast } from './composables/useToast'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const toast = useToast()

/** 导航按角色过滤：读者、馆员、管理员三端共用同一套路由与菜单。 */
const MENU = [
  {
    group: '馆藏与检索',
    roles: ['reader', 'librarian', 'admin'],
    items: [{ to: '/search', label: '图书检索', icon: '🔍' }],
  },
  {
    group: '我的',
    roles: ['reader'],
    items: [
      { to: '/my/loans', label: '借阅记录', icon: '📖' },
      { to: '/my/reservations', label: '我的预约', icon: '🔖' },
    ],
  },
  {
    group: '流通办理',
    roles: ['librarian'],
    items: [
      { to: '/circ/borrow', label: '借书办理', icon: '📥' },
      { to: '/circ/return', label: '还书办理', icon: '📤' },
      { to: '/circ/return-audit', label: '还书审核', icon: '✅' },
      { to: '/circ/charges', label: '罚款与赔偿', icon: '💰' },
      { to: '/circ/reader-records', label: '读者借阅查询', icon: '🗂️' },
    ],
  },
  {
    group: '系统管理',
    roles: ['admin'],
    items: [
      { to: '/admin/readers', label: '读者与借阅证', icon: '👥' },
      { to: '/admin/catalog', label: '馆藏维护', icon: '📚' },
      { to: '/admin/policies', label: '规则维护', icon: '⚙️' },
      { to: '/admin/reviews', label: '评论审核', icon: '💬' },
      { to: '/admin/librarians', label: '管理员账号', icon: '🧑‍💼' },
    ],
  },
]

const menus = computed(() => MENU.filter((g) => g.roles.includes(auth.role.value)))
const isBlank = computed(() => !!route.meta.blank)
const pageTitle = computed(() => route.meta.title || '图书管理系统')
const roleLabel = computed(() => ROLE_LABELS[auth.role.value] || '')

const backendOk = ref(null)

async function checkBackend() {
  try {
    await systemApi.health()
    backendOk.value = true
  } catch {
    backendOk.value = false
  }
}

async function onLogout() {
  await auth.logout()
  toast.info('已退出登录')
  router.push({ name: 'login' })
}

function onTokenExpired() {
  auth.reset()
  toast.error('登录状态已失效，请重新登录')
  router.push({ name: 'login' })
}

onMounted(() => {
  window.addEventListener('auth:expired', onTokenExpired)
  checkBackend()
})
onUnmounted(() => window.removeEventListener('auth:expired', onTokenExpired))
</script>

<template>
  <div v-if="isBlank" class="auth-host" style="height: 100%">
    <router-view />
  </div>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">📚</div>
        <div>
          <div class="brand-text">图书管理系统</div>
          <div class="brand-sub">Library Management</div>
        </div>
      </div>

      <template v-for="group in menus" :key="group.group">
        <div class="nav-group">{{ group.group }}</div>
        <router-link
          v-for="item in group.items"
          :key="item.to"
          class="nav-item"
          :to="item.to"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </template>

      <div class="sidebar-footer">
        <div class="who">
          <strong>{{ auth.displayName.value }}</strong>
          {{ roleLabel }}<template v-if="auth.cardNo.value"> · {{ auth.cardNo.value }}</template>
        </div>
        <button class="nav-item" style="width: 100%" @click="onLogout">
          <span class="nav-icon">⏏</span> 退出登录
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <h2>{{ pageTitle }}</h2>
          <div class="topbar-sub">对话式图书管理系统 · 界面层</div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px">
          <span
            class="badge"
            :class="backendOk === false ? 'badge-danger' : 'badge-success'"
          >
            <span
              style="
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: currentColor;
                display: inline-block;
              "
            />
            {{ backendOk === null ? '检测中' : backendOk ? '后端已连接' : '后端未连接' }}
          </span>
          <span class="badge badge-primary">{{ roleLabel }}</span>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>

  <ToastHost />
</template>
