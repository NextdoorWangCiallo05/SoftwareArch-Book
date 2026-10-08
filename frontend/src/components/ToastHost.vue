<script setup>
import { useToast } from '../composables/useToast'

const { toasts } = useToast()
</script>

<template>
  <div class="toast-wrap">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast-${t.type}`">
      <div v-if="t.title" class="toast-title">{{ t.title }}</div>
      <div>{{ t.message }}</div>
    </div>
  </div>
</template>
