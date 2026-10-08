<script setup>
/** 列表/详情的加载中与空态占位，统一各页面的反馈样式。 */
defineProps({
  loading: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  emptyIcon: { type: String, default: '📭' },
})
</script>

<template>
  <div v-if="loading" class="loading">
    <div class="spinner" />
    正在加载…
  </div>
  <div v-else-if="empty" class="empty">
    <div class="empty-icon">{{ emptyIcon }}</div>
    {{ emptyText }}
  </div>
  <slot v-else />
</template>
