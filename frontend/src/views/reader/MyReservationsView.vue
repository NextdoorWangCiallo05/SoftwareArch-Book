<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { reservationApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { RESERVATION_STATUS, toneOf } from '../../constants'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'

const router = useRouter()
const auth = useAuth()
const toast = useToast()

const reservations = ref([])
const loading = ref(true)
const cancellingId = ref(null)

async function load() {
  const readerId = auth.readerId.value
  if (!readerId) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await reservationApi.list(readerId)
    reservations.value = data.reservations || []
  } catch (err) {
    toast.error(err.message)
    reservations.value = []
  } finally {
    loading.value = false
  }
}

async function onCancel(reservation) {
  cancellingId.value = reservation.reservation_id
  try {
    await reservationApi.cancel(reservation.reservation_id)
    toast.success(`已取消《${reservation.title}》的预约`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    cancellingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>我的预约</h3>
          <p>同一书名下按预约先后排队，副本归还后按序通知</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && reservations.length === 0"
        empty-text="暂无预约记录"
        empty-icon="🔖"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>书名</th>
                <th>预约时间</th>
                <th>失效时间</th>
                <th>排队序号</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="resv in reservations" :key="resv.reservation_id">
                <td>
                  <a @click.prevent="router.push(`/book/${resv.title_id}`)" href="#">
                    {{ resv.title }}
                  </a>
                </td>
                <td>{{ resv.created_at?.slice(0, 19).replace('T', ' ') || '-' }}</td>
                <td>{{ resv.expires_at?.slice(0, 19).replace('T', ' ') || '-' }}</td>
                <td>{{ resv.queue_position ?? '-' }}</td>
                <td>
                  <span class="badge" :class="`badge-${toneOf(RESERVATION_STATUS, resv.status)}`">
                    {{ RESERVATION_STATUS[resv.status]?.label || resv.status }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="resv.status === 'ACTIVE'"
                    class="btn btn-sm"
                    :disabled="cancellingId === resv.reservation_id"
                    @click="onCancel(resv)"
                  >
                    {{ cancellingId === resv.reservation_id ? '处理中…' : '取消预约' }}
                  </button>
                  <span v-else class="book-meta">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </div>
  </div>
</template>
