<script setup>
import { onMounted, ref } from 'vue'

import { reviewApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const reviews = ref([])
const loading = ref(false)
const busyId = ref(null)

function starsText(value) {
  const full = Math.round(Number(value) || 0)
  return '★'.repeat(full) + '☆'.repeat(Math.max(0, 5 - full))
}

async function load() {
  loading.value = true
  try {
    const data = await reviewApi.listPending()
    reviews.value = data.reviews || []
  } catch (err) {
    toast.error(err.message)
    reviews.value = []
  } finally {
    loading.value = false
  }
}

async function moderate(review, decision) {
  busyId.value = `${review.review_id}-${decision}`
  try {
    await reviewApi.moderate(review.review_id, decision)
    toast.success(decision === 'APPROVED' ? '评论已通过，读者可见' : '评论已驳回')
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>待审核评论</h3>
          <p>读者提交或修改评论后进入待审队列，通过后才会出现在图书详情页</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && reviews.length === 0"
        empty-text="没有待审核的评论"
        empty-icon="✅"
      >
        <div
          v-for="review in reviews"
          :key="review.review_id"
          class="card"
          style="background: var(--surface-2)"
        >
          <div style="display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap">
            <div>
              <h3>《{{ review.title }}》</h3>
              <div class="book-meta">
                {{ review.reader_name || `读者 #${review.reader_id}` }} ·
                {{ review.created_at?.slice(0, 19).replace('T', ' ') }}
              </div>
            </div>
            <div class="stars" style="font-size: 17px">{{ starsText(review.rating) }}</div>
          </div>

          <p style="margin: 10px 0 14px">
            {{ review.comment || '（仅评分，未填写文字）' }}
          </p>

          <div style="display: flex; gap: 10px">
            <button
              class="btn btn-primary btn-sm"
              :disabled="busyId === `${review.review_id}-APPROVED`"
              @click="moderate(review, 'APPROVED')"
            >
              通过
            </button>
            <button
              class="btn btn-danger btn-sm"
              :disabled="busyId === `${review.review_id}-REJECTED`"
              @click="moderate(review, 'REJECTED')"
            >
              驳回
            </button>
          </div>
        </div>
      </StateBlock>
    </div>
  </div>
</template>
