<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="auth-page">
    <div class="auth-card" style="text-align: center">
      <div class="auth-mark">🧭</div>
      <h1>页面不存在</h1>
      <p class="book-meta" style="margin: 8px 0 20px">请检查地址，或返回首页继续操作。</p>
      <button class="btn btn-primary btn-block" @click="router.push('/')">返回首页</button>
    </div>
  </div>
</template>
