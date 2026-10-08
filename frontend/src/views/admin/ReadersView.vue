<script setup>
import { onMounted, reactive, ref } from 'vue'

import { adminApi } from '../../api'
import AppModal from '../../components/AppModal.vue'
import StateBlock from '../../components/StateBlock.vue'
import { READER_STATUS, READER_TYPES, readerTypeLabel, toneOf } from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const filters = reactive({ name: '', reader_type: '' })
const readers = ref([])
const total = ref(0)
const loading = ref(false)
const busyId = ref(null)

const editing = ref(null)
const editForm = reactive({ name: '', reader_type: '', email: '', phone: '' })

async function load() {
  loading.value = true
  try {
    const data = await adminApi.listReaders({
      name: filters.name.trim() || undefined,
      reader_type: filters.reader_type || undefined,
      page: 1,
      page_size: 100,
    })
    readers.value = data.readers || []
    total.value = data.total || 0
  } catch (err) {
    toast.error(err.message)
    readers.value = []
  } finally {
    loading.value = false
  }
}

function openEdit(reader) {
  editing.value = reader
  editForm.name = reader.name
  editForm.reader_type = reader.reader_type
  editForm.email = reader.email || ''
  editForm.phone = reader.phone || ''
}

async function saveEdit() {
  if (!editForm.name.trim()) {
    toast.error('姓名不能为空')
    return
  }
  busyId.value = `edit-${editing.value.reader_id}`
  try {
    await adminApi.updateReader(editing.value.reader_id, {
      name: editForm.name.trim(),
      reader_type: editForm.reader_type,
      email: editForm.email.trim() || null,
      phone: editForm.phone.trim() || null,
    })
    toast.success('读者信息已更新')
    editing.value = null
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

async function onIssueCard(reader) {
  busyId.value = `card-${reader.reader_id}`
  try {
    const card = await adminApi.issueCard(reader.reader_id)
    toast.success(`已为 ${reader.name} 办理借阅证 ${card.card_no}`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

async function onDeactivate(reader) {
  busyId.value = `off-${reader.reader_id}`
  try {
    await adminApi.deactivateReader(reader.reader_id)
    toast.success(`读者 ${reader.name} 已停用`)
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
          <h3>读者档案</h3>
          <p>共 {{ total }} 位读者；停用前需保证其无在借图书</p>
        </div>
      </div>

      <form class="inline-form" @submit.prevent="load">
        <div class="field">
          <label for="r-name">姓名</label>
          <input id="r-name" v-model="filters.name" class="input" placeholder="按姓名模糊查询" />
        </div>
        <div class="field">
          <label for="r-type">读者类型</label>
          <select id="r-type" v-model="filters.reader_type" class="select">
            <option value="">全部</option>
            <option v-for="t in READER_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <button class="btn btn-primary" type="submit">查询</button>
      </form>
    </div>

    <div class="card">
      <StateBlock
        :loading="loading"
        :empty="!loading && readers.length === 0"
        empty-text="没有符合条件的读者"
        empty-icon="👥"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>姓名</th>
                <th>类型</th>
                <th>邮箱</th>
                <th>电话</th>
                <th>状态</th>
                <th>借阅证号</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="reader in readers" :key="reader.reader_id">
                <td class="mono">#{{ reader.reader_id }}</td>
                <td>{{ reader.name }}</td>
                <td>{{ readerTypeLabel(reader.reader_type) }}</td>
                <td>{{ reader.email || '-' }}</td>
                <td>{{ reader.phone || '-' }}</td>
                <td>
                  <span
                    class="badge"
                    :class="`badge-${toneOf(READER_STATUS, reader.status)}`"
                  >
                    {{ READER_STATUS[reader.status]?.label || reader.status }}
                  </span>
                </td>
                <td class="mono">{{ reader.card_no || '未办证' }}</td>
                <td style="display: flex; gap: 6px">
                  <button class="btn btn-sm" @click="openEdit(reader)">编辑</button>
                  <button
                    v-if="!reader.card_no"
                    class="btn btn-sm btn-primary"
                    :disabled="busyId === `card-${reader.reader_id}`"
                    @click="onIssueCard(reader)"
                  >
                    办证
                  </button>
                  <button
                    v-if="reader.status === 'active'"
                    class="btn btn-sm btn-danger"
                    :disabled="busyId === `off-${reader.reader_id}`"
                    @click="onDeactivate(reader)"
                  >
                    停用
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </div>

    <AppModal
      v-if="editing"
      title="编辑读者信息"
      :subtitle="`读者 #${editing.reader_id}`"
      @close="editing = null"
    >
      <div class="field">
        <label for="e-name">姓名</label>
        <input id="e-name" v-model="editForm.name" class="input" />
      </div>
      <div class="field">
        <label for="e-type">读者类型</label>
        <select id="e-type" v-model="editForm.reader_type" class="select">
          <option v-for="t in READER_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div class="field">
        <label for="e-email">邮箱</label>
        <input id="e-email" v-model="editForm.email" class="input" />
      </div>
      <div class="field">
        <label for="e-phone">电话</label>
        <input id="e-phone" v-model="editForm.phone" class="input" />
      </div>
      <template #actions>
        <button class="btn" @click="editing = null">取消</button>
        <button class="btn btn-primary" @click="saveEdit">保存</button>
      </template>
    </AppModal>
  </div>
</template>
