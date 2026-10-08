<script setup>
import { ref } from 'vue'

import { circulationApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { LOAN_STATUS, toneOf } from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const readerId = ref('')
const statusFilter = ref('')
const loans = ref([])
const loading = ref(false)
const searched = ref(false)

const STATUS_FILTERS = [
  { value: '', label: '全部' },
  { value: 'BORROWED', label: '借阅中' },
  { value: 'OVERDUE', label: '逾期' },
  { value: 'RETURNED', label: '已归还' },
]

async function load() {
  const id = Number(readerId.value)
  if (!id) {
    toast.error('请输入读者 ID（可在「读者与借阅证」中查询）')
    return
  }
  loading.value = true
  try {
    const data = await circulationApi.records(id, statusFilter.value || undefined)
    loans.value = data.records || []
    searched.value = true
  } catch (err) {
    toast.error(err.message)
    loans.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>读者借阅查询</h3>
          <p>按读者 ID 拉取全部借阅记录，用于柜台核对与催还</p>
        </div>
      </div>

      <form class="inline-form" @submit.prevent="load">
        <div class="field">
          <label for="reader-id">读者 ID</label>
          <input id="reader-id" v-model="readerId" class="input" placeholder="如 1" />
        </div>
        <div class="field">
          <label for="status">状态</label>
          <select id="status" v-model="statusFilter" class="select">
            <option v-for="f in STATUS_FILTERS" :key="f.value" :value="f.value">
              {{ f.label }}
            </option>
          </select>
        </div>
        <button class="btn btn-primary" type="submit" :disabled="loading">查询</button>
      </form>
    </div>

    <div v-if="searched" class="card">
      <div class="card-head">
        <div>
          <h3>借阅记录</h3>
          <p>共 {{ loans.length }} 条</p>
        </div>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && loans.length === 0"
        empty-text="该读者暂无符合条件的借阅记录"
        empty-icon="🗂️"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>书名</th>
                <th>条码</th>
                <th>借出日期</th>
                <th>应还日期</th>
                <th>归还日期</th>
                <th>状态</th>
                <th>续借</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="loan in loans" :key="loan.loan_id">
                <td>{{ loan.title }}</td>
                <td class="mono">{{ loan.barcode }}</td>
                <td>{{ loan.borrow_date || '-' }}</td>
                <td>{{ loan.due_date || '-' }}</td>
                <td>{{ loan.return_date || '-' }}</td>
                <td>
                  <span class="badge" :class="`badge-${toneOf(LOAN_STATUS, loan.status)}`">
                    {{ LOAN_STATUS[loan.status]?.label || loan.status }}
                  </span>
                </td>
                <td>{{ loan.renew_count }} 次</td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </div>
  </div>
</template>
