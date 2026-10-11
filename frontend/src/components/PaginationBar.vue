<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  unit: { type: String, default: '条' },
})

const emit = defineEmits(['change'])

const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

function go(target) {
  const next = Math.min(Math.max(1, target), pageCount.value)
  if (next !== props.page) emit('change', next)
}
</script>

<template>
  <div
    v-if="total > pageSize"
    style="display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 16px"
  >
    <button class="btn btn-sm" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
    <span class="book-meta">{{ page }} / {{ pageCount }} · 共 {{ total }} {{ unit }}</span>
    <button class="btn btn-sm" :disabled="page >= pageCount" @click="go(page + 1)">下一页</button>
  </div>
</template>
