<script setup>
import { reactive, ref } from 'vue'

import { circulationApi } from '../../api'
import { money } from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const form = reactive({ barcode: '' })
const submitting = ref(false)
const lastResult = ref(null)
const history = ref([])

async function onSubmit() {
  if (!form.barcode.trim()) {
    toast.error('请填写图书条码')
    return
  }
  submitting.value = true
  try {
    const result = await circulationApi.returnBook({ barcode: form.barcode.trim() })
    lastResult.value = result
    history.value.unshift({ ...result, at: new Date().toLocaleTimeString() })
    if (history.value.length > 6) history.value.pop()
    const fine = Number(result.fine)
    if (fine > 0) {
      toast.info(`《${result.title}》已归还，产生逾期罚款 ${money(fine)} 元`, '归还成功（含罚款）')
    } else {
      toast.success(`《${result.title}》归还成功，无逾期罚款`)
    }
    form.barcode = ''
  } catch (err) {
    lastResult.value = null
    toast.error(err.message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-head">
        <div>
          <h3>还书办理</h3>
          <p>系统按罚款规则自动计算逾期天数与金额，罚款记入读者待缴清单</p>
        </div>
      </div>

      <form @submit.prevent="onSubmit">
        <div class="field">
          <label for="return-barcode">图书条码</label>
          <input
            id="return-barcode"
            v-model="form.barcode"
            class="input mono"
            placeholder="如 ITEM2026000002"
          />
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="submitting">
          {{ submitting ? '办理中…' : '确认归还' }}
        </button>
      </form>

      <div v-if="lastResult" class="alert alert-success" style="margin-top: 16px">
        <strong>归还成功</strong><br />
        《{{ lastResult.title }}》<br />
        归还日期 {{ lastResult.return_date }} · 逾期 {{ lastResult.overdue_days }} 天 · 罚款
        {{ money(lastResult.fine) }} 元
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>本次会话办理记录</h3>
          <p>含逾期与罚款金额，便于柜台当面对账</p>
        </div>
      </div>
      <div v-if="history.length === 0" class="empty">
        <div class="empty-icon">📤</div>
        还没有办理记录
      </div>
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>书名</th>
              <th>逾期</th>
              <th>罚款</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in history" :key="index">
              <td>{{ row.at }}</td>
              <td>{{ row.title }}</td>
              <td>{{ row.overdue_days }} 天</td>
              <td>¥{{ money(row.fine) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
