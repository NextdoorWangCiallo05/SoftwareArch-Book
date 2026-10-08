<script setup>
import { onMounted, reactive, ref } from 'vue'

import { adminApi } from '../../api'
import AppModal from '../../components/AppModal.vue'
import StateBlock from '../../components/StateBlock.vue'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const librarians = ref([])
const total = ref(0)
const loading = ref(false)
const busyId = ref(null)

const createForm = reactive({ username: '', password: '', name: '', employee_no: '' })
const creating = ref(false)

const editing = ref(null)
const editForm = reactive({ name: '', employee_no: '' })

async function load() {
  loading.value = true
  try {
    const data = await adminApi.listLibrarians({ page: 1, page_size: 100 })
    librarians.value = data.librarians || []
    total.value = data.total || 0
  } catch (err) {
    toast.error(err.message)
    librarians.value = []
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!createForm.username.trim() || !createForm.password || !createForm.name.trim()) {
    toast.error('用户名、密码与姓名为必填项')
    return
  }
  creating.value = true
  try {
    await adminApi.addLibrarian({
      username: createForm.username.trim(),
      password: createForm.password,
      name: createForm.name.trim(),
      employee_no: createForm.employee_no.trim() || null,
    })
    toast.success('图书管理员账号已创建')
    createForm.username = ''
    createForm.password = ''
    createForm.name = ''
    createForm.employee_no = ''
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    creating.value = false
  }
}

function openEdit(row) {
  editing.value = row
  editForm.name = row.name
  editForm.employee_no = row.employee_no || ''
}

async function saveEdit() {
  busyId.value = `edit-${editing.value.librarian_id}`
  try {
    await adminApi.updateLibrarian(editing.value.librarian_id, {
      name: editForm.name.trim() || null,
      employee_no: editForm.employee_no.trim() || null,
    })
    toast.success('管理员信息已更新')
    editing.value = null
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

async function onRemove(row) {
  busyId.value = `del-${row.librarian_id}`
  try {
    await adminApi.removeLibrarian(row.librarian_id)
    toast.success('管理员账号已删除')
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
  <div class="grid grid-2">
    <div class="card">
      <div class="card-head">
        <div>
          <h3>新建图书管理员</h3>
          <p>新建账号默认角色为「图书管理员」，可办理借还与罚款赔偿</p>
        </div>
      </div>
      <form @submit.prevent="onCreate">
        <div class="field">
          <label for="l-username">登录用户名</label>
          <input id="l-username" v-model="createForm.username" class="input" />
        </div>
        <div class="field">
          <label for="l-password">初始密码</label>
          <input id="l-password" v-model="createForm.password" class="input" type="password" />
        </div>
        <div class="field">
          <label for="l-name">姓名</label>
          <input id="l-name" v-model="createForm.name" class="input" />
        </div>
        <div class="field">
          <label for="l-emp">工号</label>
          <input id="l-emp" v-model="createForm.employee_no" class="input" />
        </div>
        <button class="btn btn-primary btn-block" type="submit" :disabled="creating">
          {{ creating ? '创建中…' : '创建账号' }}
        </button>
      </form>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>管理员账号</h3>
          <p>共 {{ total }} 个</p>
        </div>
        <button class="btn btn-sm" @click="load">刷新</button>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && librarians.length === 0"
        empty-text="暂无图书管理员"
        empty-icon="🧑‍💼"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>姓名</th>
                <th>工号</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in librarians" :key="row.librarian_id">
                <td class="mono">#{{ row.librarian_id }}</td>
                <td>{{ row.name }}</td>
                <td class="mono">{{ row.employee_no || '-' }}</td>
                <td style="display: flex; gap: 6px">
                  <button class="btn btn-sm" @click="openEdit(row)">编辑</button>
                  <button
                    class="btn btn-sm btn-danger"
                    :disabled="busyId === `del-${row.librarian_id}`"
                    @click="onRemove(row)"
                  >
                    删除
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
      title="编辑管理员"
      :subtitle="`管理员 #${editing.librarian_id}`"
      @close="editing = null"
    >
      <div class="field">
        <label for="le-name">姓名</label>
        <input id="le-name" v-model="editForm.name" class="input" />
      </div>
      <div class="field">
        <label for="le-emp">工号</label>
        <input id="le-emp" v-model="editForm.employee_no" class="input" />
      </div>
      <template #actions>
        <button class="btn" @click="editing = null">取消</button>
        <button class="btn btn-primary" @click="saveEdit">保存</button>
      </template>
    </AppModal>
  </div>
</template>
