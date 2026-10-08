<script setup>
import { onMounted, reactive, ref } from 'vue'

import { circulationApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { money } from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const tab = ref('fines') // fines | losts | report
const onlyUnpaid = ref(true)
const fines = ref([])
const losts = ref([])
const loading = ref(false)
const actingId = ref(null)

const reportForm = reactive({ barcode: '' })
const reporting = ref(false)

async function loadFines() {
  loading.value = true
  try {
    const data = await circulationApi.listFines({
      paid: onlyUnpaid.value ? false : undefined,
    })
    fines.value = data.records || []
  } catch (err) {
    toast.error(err.message)
    fines.value = []
  } finally {
    loading.value = false
  }
}

async function loadLosts() {
  loading.value = true
  try {
    const data = await circulationApi.listLosts({
      paid: onlyUnpaid.value ? false : undefined,
    })
    losts.value = data.records || []
  } catch (err) {
    toast.error(err.message)
    losts.value = []
  } finally {
    loading.value = false
  }
}

function load() {
  if (tab.value === 'fines') loadFines()
  else if (tab.value === 'losts') loadLosts()
}

function switchTab(next) {
  tab.value = next
  load()
}

async function payFine(row) {
  actingId.value = `fine-${row.fine_id}`
  try {
    await circulationApi.payFine(row.fine_id)
    toast.success(`已收取《${row.title}》的罚款 ¥${money(row.amount)}`)
    await loadFines()
  } catch (err) {
    toast.error(err.message)
  } finally {
    actingId.value = null
  }
}

async function payLost(row) {
  actingId.value = `lost-${row.lost_id}`
  try {
    await circulationApi.payLost(row.lost_id)
    toast.success(`已收取《${row.title}》的赔偿金 ¥${money(row.amount)}`)
    await loadLosts()
  } catch (err) {
    toast.error(err.message)
  } finally {
    actingId.value = null
  }
}

async function onReportLost() {
  if (!reportForm.barcode.trim()) {
    toast.error('请填写图书条码')
    return
  }
  reporting.value = true
  try {
    const result = await circulationApi.reportLost(reportForm.barcode.trim())
    toast.success(
      `《${result.title}》已登记丢失，应赔 ${money(result.amount)} 元，赔偿单号 ${result.lost_id}`,
    )
    reportForm.barcode = ''
    tab.value = 'losts'
    await loadLosts()
  } catch (err) {
    toast.error(err.message)
  } finally {
    reporting.value = false
  }
}

onMounted(loadFines)
</script>

<template>
  <div>
    <div class="card">
      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'fines' }" @click="switchTab('fines')">
          逾期罚款
        </button>
        <button class="tab" :class="{ active: tab === 'losts' }" @click="switchTab('losts')">
          丢失赔偿
        </button>
        <button class="tab" :class="{ active: tab === 'report' }" @click="switchTab('report')">
          丢失登记
        </button>
      </div>

      <template v-if="tab === 'fines'">
        <div class="card-head">
          <div>
            <h3>逾期罚款清单</h3>
            <p>还书时按罚款规则自动生成，缴纳后读者方可继续借书</p>
          </div>
          <div style="display: flex; gap: 8px; align-items: center">
            <label class="book-meta" style="display: flex; align-items: center; gap: 6px">
              <input v-model="onlyUnpaid" type="checkbox" @change="loadFines" />
              只看待缴
            </label>
            <button class="btn btn-sm" @click="loadFines">刷新</button>
          </div>
        </div>

        <StateBlock
          :loading="loading"
          :empty="!loading && fines.length === 0"
          empty-text="没有罚款记录"
          empty-icon="💰"
        >
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>罚款单号</th>
                  <th>读者</th>
                  <th>书名</th>
                  <th>金额</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in fines" :key="row.fine_id">
                  <td class="mono">#{{ row.fine_id }}</td>
                  <td>{{ row.reader_name }}<span class="book-meta"> (#{{ row.reader_id }})</span></td>
                  <td>{{ row.title }}</td>
                  <td>¥{{ money(row.amount) }}</td>
                  <td>
                    <span class="badge" :class="row.paid ? 'badge-success' : 'badge-danger'">
                      {{ row.paid ? '已缴清' : '待缴纳' }}
                    </span>
                  </td>
                  <td>
                    <button
                      v-if="!row.paid"
                      class="btn btn-sm btn-primary"
                      :disabled="actingId === `fine-${row.fine_id}`"
                      @click="payFine(row)"
                    >
                      {{ actingId === `fine-${row.fine_id}` ? '处理中…' : '收取罚款' }}
                    </button>
                    <span v-else class="book-meta">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </StateBlock>
      </template>

      <template v-else-if="tab === 'losts'">
        <div class="card-head">
          <div>
            <h3>丢失赔偿清单</h3>
            <p>赔偿金额按图书定价生成，缴纳后结案</p>
          </div>
          <div style="display: flex; gap: 8px; align-items: center">
            <label class="book-meta" style="display: flex; align-items: center; gap: 6px">
              <input v-model="onlyUnpaid" type="checkbox" @change="loadLosts" />
              只看待缴
            </label>
            <button class="btn btn-sm" @click="loadLosts">刷新</button>
          </div>
        </div>

        <StateBlock
          :loading="loading"
          :empty="!loading && losts.length === 0"
          empty-text="没有赔偿记录"
          empty-icon="📕"
        >
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>赔偿单号</th>
                  <th>读者</th>
                  <th>书名</th>
                  <th>登记日期</th>
                  <th>赔偿金额</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in losts" :key="row.lost_id">
                  <td class="mono">#{{ row.lost_id }}</td>
                  <td>{{ row.reader_name }}<span class="book-meta"> (#{{ row.reader_id }})</span></td>
                  <td>{{ row.title }}</td>
                  <td>{{ row.lost_date || '-' }}</td>
                  <td>¥{{ money(row.amount) }}</td>
                  <td>
                    <span class="badge" :class="row.paid ? 'badge-success' : 'badge-danger'">
                      {{ row.paid ? '已缴清' : '待缴纳' }}
                    </span>
                  </td>
                  <td>
                    <button
                      v-if="!row.paid"
                      class="btn btn-sm btn-primary"
                      :disabled="actingId === `lost-${row.lost_id}`"
                      @click="payLost(row)"
                    >
                      {{ actingId === `lost-${row.lost_id}` ? '处理中…' : '收取赔偿' }}
                    </button>
                    <span v-else class="book-meta">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </StateBlock>
      </template>

      <template v-else>
        <div class="card-head">
          <div>
            <h3>丢失登记</h3>
            <p>输入丢失副本的条码，系统按图书定价生成赔偿单并结束该笔借阅</p>
          </div>
        </div>
        <form class="inline-form" @submit.prevent="onReportLost">
          <div class="field">
            <label for="lost-barcode">图书条码</label>
            <input
              id="lost-barcode"
              v-model="reportForm.barcode"
              class="input mono"
              placeholder="如 ITEM2026000003"
            />
          </div>
          <button class="btn btn-danger" type="submit" :disabled="reporting">
            {{ reporting ? '登记中…' : '登记丢失并生成赔偿单' }}
          </button>
        </form>
      </template>
    </div>

    <div v-if="tab === 'report'" class="alert alert-info" style="margin-top: 16px">
      丢失登记只对处于「借阅中」的副本有效；登记后该副本标记为已丢失，读者需缴纳赔偿金。
    </div>
  </div>
</template>
