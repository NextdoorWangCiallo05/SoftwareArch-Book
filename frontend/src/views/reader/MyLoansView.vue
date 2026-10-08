<script setup>
import { onMounted, ref } from 'vue'

import { circulationApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { LOAN_STATUS, toneOf } from '../../constants'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'

const auth = useAuth()
const toast = useToast()

const STATUS_FILTERS = [
  { value: '', label: '全部' },
  { value: 'BORROWED', label: '借阅中' },
  { value: 'RETURN_REQUESTED', label: '待审核归还' },
  { value: 'OVERDUE', label: '逾期' },
  { value: 'RETURNED', label: '已归还' },
]

const statusFilter = ref('')
const loans = ref([])
const loading = ref(true)
const renewingId = ref(null)
const returningId = ref(null)

async function load() {
  const readerId = auth.readerId.value
  if (!readerId) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await circulationApi.records(readerId, statusFilter.value || undefined)
    loans.value = data.records || []
  } catch (err) {
    toast.error(err.message)
    loans.value = []
  } finally {
    loading.value = false
  }
}

async function onRenew(loan) {
  renewingId.value = loan.loan_id
  try {
    const result = await circulationApi.renew(loan.loan_id)
    toast.success(`《${result.title}》续借成功，新应还日期 ${result.new_due_date}`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    renewingId.value = null
  }
}

async function onRequestReturn(loan) {
  returningId.value = loan.loan_id
  try {
    await circulationApi.requestReturn(loan.loan_id)
    toast.success(`《${loan.title}》归还申请已提交，请将图书交至馆台等待审核`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    returningId.value = null
  }
}

function onFilterChange(value) {
  statusFilter.value = value
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>我的借阅记录</h3>
          <p>借阅证号 {{ auth.cardNo.value || '（未办证）' }}</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <div class="tabs">
        <button
          v-for="f in STATUS_FILTERS"
          :key="f.value"
          class="tab"
          :class="{ active: statusFilter === f.value }"
          @click="onFilterChange(f.value)"
        >
          {{ f.label }}
        </button>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && loans.length === 0"
        empty-text="暂无借阅记录"
        empty-icon="📖"
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
                <th>操作</th>
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
                <td>
                  <div
                    v-if="loan.status === 'BORROWED'"
                    style="display: flex; gap: 8px; flex-wrap: wrap"
                  >
                    <button
                      class="btn btn-sm"
                      :disabled="renewingId === loan.loan_id || returningId === loan.loan_id"
                      @click="onRenew(loan)"
                    >
                      {{ renewingId === loan.loan_id ? '处理中…' : '续借' }}
                    </button>
                    <button
                      class="btn btn-sm btn-primary"
                      :disabled="renewingId === loan.loan_id || returningId === loan.loan_id"
                      @click="onRequestReturn(loan)"
                    >
                      {{ returningId === loan.loan_id ? '提交中…' : '申请归还' }}
                    </button>
                  </div>
                  <span v-else-if="loan.status === 'RETURN_REQUESTED'" class="book-meta">
                    等待馆员审核
                  </span>
                  <span v-else class="book-meta">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </div>

    <div class="alert alert-info" style="margin-top: 16px">
      续借需满足：账号无未缴罚款、未超过最大续借次数、图书未被他人预约。<br />
      归还流程：点击「申请归还」提交申请并将图书交至馆台，馆员在「还书审核」中确认收书后完成归还；
      审核通过前图书仍计入在借，且不可续借。
    </div>
  </div>
</template>
