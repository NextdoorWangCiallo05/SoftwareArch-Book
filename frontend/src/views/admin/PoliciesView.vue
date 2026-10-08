<script setup>
import { onMounted, reactive, ref } from 'vue'

import { adminApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import {
  FINE_CATEGORIES,
  ITEM_TYPES,
  READER_TYPES,
  fineCategoryLabel,
  itemTypeLabel,
  readerTypeLabel,
} from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const policies = ref([])
const fineRules = ref([])
const loading = ref(false)
const saving = ref(false)

const policyForm = reactive({
  reader_type: 'UNDERGRADUATE',
  item_type: 'ALL',
  max_borrow_count: 5,
  borrow_days: 30,
})

const fineForm = reactive({
  item_category: 'CHINESE_BOOK',
  grace_days: 0,
  amount_per_day: 0.5,
})

async function load() {
  loading.value = true
  try {
    const [p, f] = await Promise.all([
      adminApi.listBorrowPolicies(),
      adminApi.listFineRules(),
    ])
    policies.value = p.policies || []
    fineRules.value = f.rules || []
  } catch (err) {
    toast.error(err.message)
  } finally {
    loading.value = false
  }
}

async function savePolicy() {
  saving.value = true
  try {
    await adminApi.upsertBorrowPolicy({
      reader_type: policyForm.reader_type,
      item_type: policyForm.item_type,
      max_borrow_count: Number(policyForm.max_borrow_count),
      borrow_days: Number(policyForm.borrow_days),
    })
    toast.success('借阅规则已保存（同读者类型 + 类型组合将被覆盖）')
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    saving.value = false
  }
}

async function saveFineRule() {
  saving.value = true
  try {
    await adminApi.upsertFineRule({
      item_category: fineForm.item_category,
      grace_days: Number(fineForm.grace_days),
      amount_per_day: Number(fineForm.amount_per_day),
    })
    toast.success('罚款规则已保存')
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    saving.value = false
  }
}

function usePolicyRow(row) {
  policyForm.reader_type = row.reader_type
  policyForm.item_type = row.item_type
  policyForm.max_borrow_count = row.max_borrow_count
  policyForm.borrow_days = row.borrow_days
}

function useFineRow(row) {
  fineForm.item_category = row.item_category
  fineForm.grace_days = row.grace_days
  fineForm.amount_per_day = row.amount_per_day
}

onMounted(load)
</script>

<template>
  <div class="grid grid-2">
    <div class="card">
      <div class="card-head">
        <div>
          <h3>借阅规则</h3>
          <p>定义每种读者类型可借册数与借期；item_type 为 ALL 表示适用于全部类型</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock :loading="loading" :empty="!loading && policies.length === 0" empty-text="尚未配置借阅规则" empty-icon="📋">
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>读者类型</th>
                <th>出借物类型</th>
                <th>可借册数</th>
                <th>借期（天）</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in policies" :key="index">
                <td>{{ readerTypeLabel(row.reader_type) }}</td>
                <td>{{ row.item_type === 'ALL' ? '全部' : itemTypeLabel(row.item_type) }}</td>
                <td>{{ row.max_borrow_count }}</td>
                <td>{{ row.borrow_days }}</td>
                <td>
                  <button class="btn btn-sm" @click="usePolicyRow(row)">载入</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>

      <form class="card" style="background: var(--surface-2); margin-top: 14px" @submit.prevent="savePolicy">
        <h3 style="margin-bottom: 10px">新增 / 覆盖规则</h3>
        <div class="grid grid-2">
          <div class="field">
            <label for="p-reader">读者类型</label>
            <select id="p-reader" v-model="policyForm.reader_type" class="select">
              <option v-for="t in READER_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="p-item">出借物类型</label>
            <select id="p-item" v-model="policyForm.item_type" class="select">
              <option value="ALL">全部</option>
              <option v-for="t in ITEM_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="p-max">可借册数</label>
            <input id="p-max" v-model="policyForm.max_borrow_count" class="input" type="number" min="1" />
          </div>
          <div class="field">
            <label for="p-days">借期（天）</label>
            <input id="p-days" v-model="policyForm.borrow_days" class="input" type="number" min="1" />
          </div>
        </div>
        <button class="btn btn-primary" type="submit" :disabled="saving">保存借阅规则</button>
      </form>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>罚款规则</h3>
          <p>逾期超过宽限期后，按天累计罚款，还书时自动结算</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock :loading="loading" :empty="!loading && fineRules.length === 0" empty-text="尚未配置罚款规则" empty-icon="💰">
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>罚款类别</th>
                <th>宽限期（天）</th>
                <th>每天金额</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in fineRules" :key="index">
                <td>{{ fineCategoryLabel(row.item_category) }}</td>
                <td>{{ row.grace_days }}</td>
                <td>¥{{ Number(row.amount_per_day).toFixed(2) }}</td>
                <td>
                  <button class="btn btn-sm" @click="useFineRow(row)">载入</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>

      <form class="card" style="background: var(--surface-2); margin-top: 14px" @submit.prevent="saveFineRule">
        <h3 style="margin-bottom: 10px">新增 / 覆盖规则</h3>
        <div class="field">
          <label for="f-category">罚款类别</label>
          <select id="f-category" v-model="fineForm.item_category" class="select">
            <option v-for="c in FINE_CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
        <div class="grid grid-2">
          <div class="field">
            <label for="f-grace">宽限期（天）</label>
            <input id="f-grace" v-model="fineForm.grace_days" class="input" type="number" min="0" />
          </div>
          <div class="field">
            <label for="f-amount">每天金额</label>
            <input id="f-amount" v-model="fineForm.amount_per_day" class="input" type="number" step="0.01" min="0" />
          </div>
        </div>
        <button class="btn btn-primary" type="submit" :disabled="saving">保存罚款规则</button>
      </form>
    </div>
  </div>
</template>
