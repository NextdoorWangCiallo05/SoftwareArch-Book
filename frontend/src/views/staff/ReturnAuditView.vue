<script setup>
import { onMounted, ref } from 'vue'

import { circulationApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { money } from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const requests = ref([])
const loading = ref(true)
const actingId = ref(null)

async function load() {
  loading.value = true
  try {
    const data = await circulationApi.listReturnRequests()
    requests.value = data.records || []
  } catch (err) {
    toast.error(err.message)
    requests.value = []
  } finally {
    loading.value = false
  }
}

async function onApprove(row) {
  actingId.value = row.loan_id
  try {
    const result = await circulationApi.approveReturn(row.loan_id)
    const fine = Number(result.fine)
    if (fine > 0) {
      toast.info(
        `《${result.title}》归还成功，逾期 ${result.overdue_days} 天，罚款 ${money(fine)} 元`,
        '审核通过（含罚款）',
      )
    } else {
      toast.success(`《${result.title}》归还成功，无逾期罚款`)
    }
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    actingId.value = null
  }
}

async function onReject(row) {
  actingId.value = row.loan_id
  try {
    await circulationApi.rejectReturn(row.loan_id)
    toast.info(`《${row.title}》的归还申请已驳回，借阅记录恢复为借阅中`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    actingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>还书审核</h3>
          <p>读者在线提交归还申请后由馆员确认收书；通过即完成归还并自动结算逾期罚款</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && requests.length === 0"
        empty-text="暂无待审核的归还申请"
        empty-icon="📥"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>借阅号</th>
                <th>读者</th>
                <th>书名</th>
                <th>条码</th>
                <th>借出日期</th>
                <th>应还日期</th>
                <th>逾期</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in requests" :key="row.loan_id">
                <td class="mono">#{{ row.loan_id }}</td>
                <td>{{ row.reader_name }}</td>
                <td>{{ row.title }}</td>
                <td class="mono">{{ row.barcode }}</td>
                <td>{{ row.borrow_date || '-' }}</td>
                <td>{{ row.due_date || '-' }}</td>
                <td>
                  <span v-if="row.is_overdue" class="badge badge-danger">已逾期</span>
                  <span v-else class="book-meta">-</span>
                </td>
                <td>
                  <div style="display: flex; gap: 8px">
                    <button
                      class="btn btn-sm btn-primary"
                      :disabled="actingId === row.loan_id"
                      @click="onApprove(row)"
                    >
                      {{ actingId === row.loan_id ? '处理中…' : '确认收书' }}
                    </button>
                    <button
                      class="btn btn-sm"
                      :disabled="actingId === row.loan_id"
                      @click="onReject(row)"
                    >
                      驳回
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </div>

    <div class="alert alert-info" style="margin-top: 16px">
      读者也可到馆台现场还书，由馆员在「还书办理」中凭条码直接办理，无需读者先提交申请。
    </div>
  </div>
</template>
