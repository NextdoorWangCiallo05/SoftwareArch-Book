/**
 * 全局登录态。以模块级 reactive 对象做简易 store，避免引入额外状态管理依赖。
 * profile 结构对应后端 ProfileDTO：{ user_id, username, role, reader_id, name, reader_type, card_no }
 */
import { computed, reactive } from 'vue'

import { authApi } from '../api'
import { clearToken, getToken, setToken } from '../api/http'

const state = reactive({
  profile: null,
  ready: false, // 首次鉴权探测是否完成
})

/**
 * 各角色登录后的默认落地页。
 * 管理员没有流通权限（BR-011），故落到系统管理首页，避免落到 403 页面。
 */
export function homeRoute(role) {
  if (role === 'librarian') return { name: 'circ-borrow' }
  if (role === 'admin') return { name: 'admin-readers' }
  return { name: 'search' }
}

export function useAuth() {
  const isLoggedIn = computed(() => !!state.profile)
  const role = computed(() => state.profile?.role || '')
  const isReader = computed(() => role.value === 'reader')
  /** 后端 BR-011：流通办理（借还/续借/罚款赔偿）仅图书管理员，系统管理员不代办。 */
  const isStaff = computed(() => role.value === 'librarian')
  const isAdmin = computed(() => role.value === 'admin')
  const readerId = computed(() => state.profile?.reader_id ?? null)
  const cardNo = computed(() => state.profile?.card_no ?? '')
  const displayName = computed(() => state.profile?.name || state.profile?.username || '')

  async function login(username, password) {
    const data = await authApi.login({ username, password })
    setToken(data.token)
    await loadProfile()
    return data
  }

  function register(payload) {
    return authApi.register(payload)
  }

  /** 冷启动：若本地有令牌则换取身份，失败则视为未登录。 */
  async function loadProfile() {
    if (!getToken()) {
      state.profile = null
      state.ready = true
      return null
    }
    try {
      state.profile = await authApi.me()
    } catch {
      clearToken()
      state.profile = null
    }
    state.ready = true
    return state.profile
  }

  async function logout() {
    try {
      if (getToken()) await authApi.logout()
    } catch {
      // 退出失败不影响本地清理
    }
    reset()
  }

  function reset() {
    clearToken()
    state.profile = null
  }

  return {
    state,
    isLoggedIn,
    role,
    isReader,
    isStaff,
    isAdmin,
    readerId,
    cardNo,
    displayName,
    login,
    register,
    loadProfile,
    logout,
    reset,
  }
}
