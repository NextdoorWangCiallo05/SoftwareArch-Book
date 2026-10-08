<script setup>
import { reactive, ref } from 'vue'

import { circulationApi } from '../../api'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const form = reactive({ card_no: '', barcode: '' })
const submitting = ref(false)
const lastResult = ref(null)
const history = ref([])

async function onSubmit() {
  if (!form.card_no.trim() || !form.barcode.trim()) {
    toast.error('请填写借阅证号与图书条码')
    return
  }
  submitting.value = true
  try {
    const result = await circulationApi.borrow({
      card_no: form.card_no.trim(),
      barcode: form.barcode.trim(),
    })
    lastResult.value = result
    history.value.unshift({ ...result, at: new Date().toLocaleTimeString() })
    if (history.value.length > 6) history.value.pop()
    toast.success(`《${result.title}》借出成功，应还日期 ${result.due_date}`)
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
          <h3>借书办理</h3>
          <p>借阅由图书管理员代理，需同时校验读者借阅证与馆藏条码</p>
        </div>
      </div>

      <form @submit.prevent="onSubmit">
        <div class="field">
          <label for="card">借阅证号</label>
          <input id="card" v-model="form.card_no" class="input mono" placeholder="如 CARD2026000001" />
        </div>
        <div class="field">
          <label for="barcode">图书条码</label>
          <input id="barcode" v-model="form.barcode" class="input mono" placeholder="如 ITEM2026000002" />
          <span class="hint">条码可在「图书检索 → 详情 → 馆藏副本」中查看</span>
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="submitting">
          {{ submitting ? '办理中…' : '确认借出' }}
        </button>
      </form>

      <div v-if="lastResult" class="alert alert-success" style="margin-top: 16px">
        <strong>办理成功</strong><br />
        《{{ lastResult.title }}》（{{ lastResult.barcode }}）<br />
        借出日期 {{ lastResult.borrow_date }} · 应还日期 {{ lastResult.due_date }}
      </div>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>本次会话办理记录</h3>
          <p>仅用于柜台核对，刷新页面即清空</p>
        </div>
      </div>
      <div v-if="history.length === 0" class="empty">
        <div class="empty-icon">📥</div>
        还没有办理记录
      </div>
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>书名</th>
              <th>应还日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in history" :key="index">
              <td>{{ row.at }}</td>
              <td>{{ row.title }}</td>
              <td>{{ row.due_date }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="alert alert-info" style="margin-top: 16px">
        借出会被这些规则拒绝：读者被停用、证已失效、超出可借册数、有未缴罚款、副本不可借。
      </div>
    </div>
  </div>
</template>
