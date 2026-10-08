<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})
const emit = defineEmits(['close'])
</script>

<template>
  <div class="modal-mask" @click.self="emit('close')">
    <div class="modal">
      <h3>{{ title }}</h3>
      <p v-if="subtitle" class="book-meta" style="margin-bottom: 14px">{{ subtitle }}</p>
      <slot />
      <div class="modal-actions">
        <slot name="actions">
          <button class="btn" @click="emit('close')">关闭</button>
        </slot>
      </div>
    </div>
  </div>
</template>
