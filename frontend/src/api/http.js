/**
 * HTTP 客户端：统一处理后端 {code, message, data} 信封与 Bearer 令牌。
 *
 * 约定：后端业务错误返回的 HTTP 状态码等于信封中的 code（400/403/404/500），
 * 故非 2xx 时统一抛出 ApiError，由页面捕获后提示 message。
 */

const TOKEN_KEY = 'library.token'

export class ApiError extends Error {
  constructor(message, code) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/** 令牌失效时广播事件，由 App.vue 统一跳转登录页，避免此处依赖 router。 */
function notifyAuthExpired() {
  window.dispatchEvent(new CustomEvent('auth:expired'))
}

async function request(method, path, { body, params, auth = true } = {}) {
  let url = path
  if (params) {
    const search = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') search.append(key, value)
    }
    const qs = search.toString()
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }

  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError('无法连接后端服务，请确认 backend 已在 8001 端口启动', 0)
  }

  let payload = null
  try {
    payload = await res.json()
  } catch {
    payload = null
  }

  if (!res.ok) {
    const message = payload?.message || `请求失败（HTTP ${res.status}）`
    // 仅"令牌无效"才清理登录态；普通权限不足（403）不应踢出登录
    if (res.status === 403 && /未登录|令牌/.test(message)) {
      clearToken()
      notifyAuthExpired()
    }
    throw new ApiError(message, payload?.code ?? res.status)
  }

  return payload ? payload.data : null
}

export const http = {
  get: (path, options) => request('GET', path, options),
  post: (path, body, options) => request('POST', path, { ...options, body }),
  put: (path, body, options) => request('PUT', path, { ...options, body }),
  del: (path, options) => request('DELETE', path, options),
}
