/** 轻量全局提示。接口异常统一走 error() 展示后端返回的 message。 */
import { reactive } from 'vue'

const toasts = reactive([])
let seq = 0
const DURATION = 3800

export function useToast() {
  function push(type, message, title = '') {
    const id = ++seq
    toasts.push({ id, type, message, title })
    setTimeout(() => {
      const index = toasts.findIndex((t) => t.id === id)
      if (index >= 0) toasts.splice(index, 1)
    }, DURATION)
  }

  return {
    toasts,
    success: (message, title = '操作成功') => push('success', message, title),
    error: (message, title = '操作失败') => push('error', message, title),
    info: (message, title = '提示') => push('info', message, title),
  }
}
