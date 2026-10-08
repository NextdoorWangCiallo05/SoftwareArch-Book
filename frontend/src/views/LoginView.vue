<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { READER_TYPES } from '../constants'
import { homeRoute, useAuth } from '../composables/useAuth'
import { useToast } from '../composables/useToast'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const toast = useToast()

const mode = ref('login') // login | register
const submitting = ref(false)
const errorMessage = ref('')

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({
  username: '',
  password: '',
  name: '',
  reader_type: 'UNDERGRADUATE',
  email: '',
})

const DEMO_ACCOUNTS = [
  { label: '读者 zhangsan', username: 'zhangsan', password: '123456' },
  { label: '图书管理员 lib01', username: 'lib01', password: '123456' },
  { label: '系统管理员 admin', username: 'admin', password: 'admin123' },
]

function fillDemo(account) {
  mode.value = 'login'
  loginForm.username = account.username
  loginForm.password = account.password
  errorMessage.value = ''
}

async function onLogin() {
  errorMessage.value = ''
  if (!loginForm.username || !loginForm.password) {
    errorMessage.value = '请输入用户名与密码'
    return
  }
  submitting.value = true
  try {
    const data = await auth.login(loginForm.username.trim(), loginForm.password)
    toast.success(`欢迎回来，${data.username}`)
    const target = route.query.redirect
    if (typeof target === 'string' && target) router.push(target)
    else router.push(homeRoute(data.role))
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    submitting.value = false
  }
}

async function onRegister() {
  errorMessage.value = ''
  if (!registerForm.username || !registerForm.password || !registerForm.name) {
    errorMessage.value = '用户名、密码与姓名为必填项'
    return
  }
  submitting.value = true
  try {
    await auth.register({
      username: registerForm.username.trim(),
      password: registerForm.password,
      name: registerForm.name.trim(),
      reader_type: registerForm.reader_type,
      email: registerForm.email || null,
    })
    toast.success('注册成功，请使用新账号登录')
    loginForm.username = registerForm.username.trim()
    loginForm.password = ''
    mode.value = 'login'
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-mark">📚</div>
        <h1>图书管理系统</h1>
        <p>{{ mode === 'login' ? '登录以继续借阅与管理' : '注册读者账号' }}</p>
      </div>

      <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

      <form v-if="mode === 'login'" @submit.prevent="onLogin">
        <div class="field">
          <label for="login-username">用户名</label>
          <input
            id="login-username"
            v-model="loginForm.username"
            class="input"
            autocomplete="username"
            placeholder="例如 zhangsan"
          />
        </div>
        <div class="field">
          <label for="login-password">密码</label>
          <input
            id="login-password"
            v-model="loginForm.password"
            class="input"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="submitting">
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>

      <form v-else @submit.prevent="onRegister">
        <div class="field">
          <label for="reg-username">用户名</label>
          <input id="reg-username" v-model="registerForm.username" class="input" placeholder="登录名" />
        </div>
        <div class="field">
          <label for="reg-password">密码</label>
          <input id="reg-password" v-model="registerForm.password" class="input" type="password" />
        </div>
        <div class="field">
          <label for="reg-name">姓名</label>
          <input id="reg-name" v-model="registerForm.name" class="input" />
        </div>
        <div class="field">
          <label for="reg-type">读者类型</label>
          <select id="reg-type" v-model="registerForm.reader_type" class="select">
            <option v-for="t in READER_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <div class="field">
          <label for="reg-email">邮箱（选填）</label>
          <input id="reg-email" v-model="registerForm.email" class="input" type="email" />
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="submitting">
          {{ submitting ? '提交中…' : '注册' }}
        </button>
      </form>

      <div style="margin-top: 14px; text-align: center; font-size: 13px">
        <a
          href="#"
          @click.prevent="
            mode = mode === 'login' ? 'register' : 'login';
            errorMessage = ''
          "
        >
          {{ mode === 'login' ? '还没有账号？注册读者账号' : '已有账号？返回登录' }}
        </a>
      </div>

      <div v-if="mode === 'login'" class="demo-accounts">
        <p>演示账号（点击自动填充）</p>
        <div class="demo-list">
          <button
            v-for="acc in DEMO_ACCOUNTS"
            :key="acc.username"
            class="demo-item"
            type="button"
            @click="fillDemo(acc)"
          >
            <span>{{ acc.label }}</span>
            <span class="mono">{{ acc.username }} / {{ acc.password }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
