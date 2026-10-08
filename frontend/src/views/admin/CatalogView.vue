<script setup>
import { onMounted, reactive, ref } from 'vue'

import { adminApi, catalogApi } from '../../api'
import AppModal from '../../components/AppModal.vue'
import StateBlock from '../../components/StateBlock.vue'
import {
  FINE_CATEGORIES,
  ITEM_STATUS,
  ITEM_TYPES,
  itemTypeLabel,
  toneOf,
} from '../../constants'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const filters = reactive({ keyword: '', author: '', category: '', item_type: '' })
const books = ref([])
const total = ref(0)
const loading = ref(false)
const busyId = ref(null)

/* ---- 新增图书 ---- */
const showCreate = ref(false)
const createForm = reactive({
  title: '',
  author: '',
  isbn: '',
  publisher: '',
  published_year: '',
  category: '',
  item_type: 'BOOK',
  price: '',
})
const creating = ref(false)

/* ---- 编辑图书 ---- */
const editing = ref(null)
const editForm = reactive({
  title: '',
  author: '',
  publisher: '',
  published_year: '',
  category: '',
  price: '',
})

/* ---- 副本管理 ---- */
const itemModal = ref(null) // { title_id, title, items }
const itemsLoading = ref(false)
const addItemForm = reactive({ count: 1, location: '', fine_category: '' })
const addingItems = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await catalogApi.search({
      keyword: filters.keyword.trim() || undefined,
      author: filters.author.trim() || undefined,
      category: filters.category.trim() || undefined,
      item_type: filters.item_type || undefined,
      page: 1,
      page_size: 100,
    })
    books.value = data.books || []
    total.value = data.total || 0
  } catch (err) {
    toast.error(err.message)
    books.value = []
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!createForm.title.trim() || !createForm.author.trim() || !createForm.isbn.trim()) {
    toast.error('书名、作者与 ISBN 为必填项')
    return
  }
  creating.value = true
  try {
    await adminApi.addTitle({
      title: createForm.title.trim(),
      author: createForm.author.trim(),
      isbn: createForm.isbn.trim(),
      publisher: createForm.publisher.trim() || null,
      published_year: createForm.published_year ? Number(createForm.published_year) : null,
      category: createForm.category.trim() || null,
      item_type: createForm.item_type,
      price: createForm.price ? Number(createForm.price) : null,
    })
    toast.success('图书已添加，可继续为其添加馆藏副本')
    createForm.title = ''
    createForm.author = ''
    createForm.isbn = ''
    createForm.publisher = ''
    createForm.published_year = ''
    createForm.category = ''
    createForm.price = ''
    showCreate.value = false
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    creating.value = false
  }
}

function openEdit(book) {
  editing.value = book
  editForm.title = book.title
  editForm.author = book.author
  editForm.publisher = ''
  editForm.published_year = ''
  editForm.category = book.category || ''
  editForm.price = ''
}

async function saveEdit() {
  busyId.value = `edit-${editing.value.title_id}`
  try {
    await adminApi.updateTitle(editing.value.title_id, {
      title: editForm.title.trim() || null,
      author: editForm.author.trim() || null,
      publisher: editForm.publisher.trim() || null,
      published_year: editForm.published_year ? Number(editForm.published_year) : null,
      category: editForm.category.trim() || null,
      price: editForm.price ? Number(editForm.price) : null,
    })
    toast.success('图书信息已更新')
    editing.value = null
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

async function onDeactivate(book) {
  busyId.value = `off-${book.title_id}`
  try {
    await adminApi.deactivateTitle(book.title_id)
    toast.success(`《${book.title}》已下架`)
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    busyId.value = null
  }
}

async function openItems(book) {
  itemModal.value = { title_id: book.title_id, title: book.title, items: [] }
  addItemForm.count = 1
  addItemForm.location = ''
  addItemForm.fine_category = ''
  await reloadItems()
}

async function reloadItems() {
  itemsLoading.value = true
  try {
    const detail = await catalogApi.detail(itemModal.value.title_id)
    itemModal.value.items = detail.items || []
  } catch (err) {
    toast.error(err.message)
  } finally {
    itemsLoading.value = false
  }
}

async function onAddItems() {
  const count = Number(addItemForm.count)
  if (!count || count < 1) {
    toast.error('副本数量至少为 1')
    return
  }
  addingItems.value = true
  try {
    const data = await adminApi.addItems({
      title_id: itemModal.value.title_id,
      count,
      location: addItemForm.location.trim() || null,
      fine_category: addItemForm.fine_category || null,
    })
    toast.success(`已添加 ${data.items.length} 个副本`)
    addItemForm.count = 1
    addItemForm.location = ''
    await reloadItems()
    await load()
  } catch (err) {
    toast.error(err.message)
  } finally {
    addingItems.value = false
  }
}

async function onRemoveItem(item) {
  busyId.value = `item-${item.item_id}`
  try {
    await adminApi.removeItem(item.item_id)
    toast.success(`副本 ${item.barcode} 已删除`)
    await reloadItems()
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
          <h3>馆藏检索与维护</h3>
          <p>共 {{ total }} 种图书；下架前需保证无未归还副本</p>
        </div>
        <button class="btn btn-primary btn-sm" @click="showCreate = !showCreate">
          {{ showCreate ? '收起新增表单' : '+ 新增图书' }}
        </button>
      </div>

      <form v-if="showCreate" class="card" style="background: var(--surface-2)" @submit.prevent="onCreate">
        <div class="grid grid-3">
          <div class="field">
            <label for="c-title">书名 *</label>
            <input id="c-title" v-model="createForm.title" class="input" />
          </div>
          <div class="field">
            <label for="c-author">作者 *</label>
            <input id="c-author" v-model="createForm.author" class="input" />
          </div>
          <div class="field">
            <label for="c-isbn">ISBN *</label>
            <input id="c-isbn" v-model="createForm.isbn" class="input mono" />
          </div>
          <div class="field">
            <label for="c-pub">出版社</label>
            <input id="c-pub" v-model="createForm.publisher" class="input" />
          </div>
          <div class="field">
            <label for="c-year">出版年</label>
            <input id="c-year" v-model="createForm.published_year" class="input" type="number" />
          </div>
          <div class="field">
            <label for="c-cat">分类</label>
            <input id="c-cat" v-model="createForm.category" class="input" />
          </div>
          <div class="field">
            <label for="c-type">类型</label>
            <select id="c-type" v-model="createForm.item_type" class="select">
              <option v-for="t in ITEM_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="c-price">定价</label>
            <input id="c-price" v-model="createForm.price" class="input" type="number" step="0.01" />
          </div>
        </div>
        <button class="btn btn-primary" type="submit" :disabled="creating">
          {{ creating ? '提交中…' : '保存图书' }}
        </button>
      </form>

      <form class="inline-form" style="margin-top: 14px" @submit.prevent="load">
        <div class="field">
          <label for="f-kw">书名关键词</label>
          <input id="f-kw" v-model="filters.keyword" class="input" />
        </div>
        <div class="field">
          <label for="f-author">作者</label>
          <input id="f-author" v-model="filters.author" class="input" />
        </div>
        <div class="field">
          <label for="f-cat">分类</label>
          <input id="f-cat" v-model="filters.category" class="input" />
        </div>
        <div class="field">
          <label for="f-type">类型</label>
          <select id="f-type" v-model="filters.item_type" class="select">
            <option value="">全部</option>
            <option v-for="t in ITEM_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <button class="btn btn-primary" type="submit">查询</button>
      </form>
    </div>

    <div class="card">
      <StateBlock
        :loading="loading"
        :empty="!loading && books.length === 0"
        empty-text="没有符合条件的图书"
        empty-icon="📚"
      >
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>书名</th>
                <th>作者</th>
                <th>ISBN</th>
                <th>类型</th>
                <th>分类</th>
                <th>可借</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="book in books" :key="book.title_id">
                <td class="mono">#{{ book.title_id }}</td>
                <td>{{ book.title }}</td>
                <td>{{ book.author }}</td>
                <td class="mono">{{ book.isbn }}</td>
                <td>{{ itemTypeLabel(book.item_type) }}</td>
                <td>{{ book.category || '-' }}</td>
                <td>
                  <span class="badge" :class="book.available_count > 0 ? 'badge-success' : 'badge-neutral'">
                    {{ book.available_count }}
                  </span>
                </td>
                <td style="display: flex; gap: 6px; flex-wrap: wrap">
                  <button class="btn btn-sm" @click="openEdit(book)">编辑</button>
                  <button class="btn btn-sm" @click="openItems(book)">副本</button>
                  <button
                    class="btn btn-sm btn-danger"
                    :disabled="busyId === `off-${book.title_id}`"
                    @click="onDeactivate(book)"
                  >
                    下架
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
      title="编辑图书信息"
      :subtitle="`《${editing.title}》 · ISBN ${editing.isbn}（不可修改）`"
      @close="editing = null"
    >
      <div class="field">
        <label for="e-title">书名</label>
        <input id="e-title" v-model="editForm.title" class="input" />
      </div>
      <div class="field">
        <label for="e-author">作者</label>
        <input id="e-author" v-model="editForm.author" class="input" />
      </div>
      <div class="field">
        <label for="e-pub">出版社</label>
        <input id="e-pub" v-model="editForm.publisher" class="input" placeholder="留空表示不修改" />
      </div>
      <div class="field">
        <label for="e-year">出版年</label>
        <input id="e-year" v-model="editForm.published_year" class="input" type="number" />
      </div>
      <div class="field">
        <label for="e-cat">分类</label>
        <input id="e-cat" v-model="editForm.category" class="input" />
      </div>
      <div class="field">
        <label for="e-price">定价</label>
        <input id="e-price" v-model="editForm.price" class="input" type="number" step="0.01" />
      </div>
      <template #actions>
        <button class="btn" @click="editing = null">取消</button>
        <button class="btn btn-primary" @click="saveEdit">保存</button>
      </template>
    </AppModal>

    <AppModal
      v-if="itemModal"
      title="馆藏副本管理"
      :subtitle="`《${itemModal.title}》`"
      @close="itemModal = null"
    >
      <div class="card" style="background: var(--surface-2)">
        <h3 style="margin-bottom: 10px">添加副本</h3>
        <div class="inline-form">
          <div class="field">
            <label for="n-count">数量</label>
            <input id="n-count" v-model="addItemForm.count" class="input" type="number" min="1" />
          </div>
          <div class="field">
            <label for="n-loc">馆藏位置</label>
            <input id="n-loc" v-model="addItemForm.location" class="input" placeholder="如 A区3排" />
          </div>
          <div class="field">
            <label for="n-fine">罚款类别</label>
            <select id="n-fine" v-model="addItemForm.fine_category" class="select">
              <option value="">按类型默认</option>
              <option v-for="c in FINE_CATEGORIES" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
          </div>
          <button class="btn btn-primary" :disabled="addingItems" @click="onAddItems">
            {{ addingItems ? '添加中…' : '添加' }}
          </button>
        </div>
      </div>

      <StateBlock :loading="itemsLoading" :empty="!itemsLoading && itemModal.items.length === 0" empty-text="暂无副本" empty-icon="📦">
        <div class="table-wrap" style="margin-top: 12px">
          <table class="table">
            <thead>
              <tr>
                <th>条码</th>
                <th>状态</th>
                <th>位置</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in itemModal.items" :key="item.item_id">
                <td class="mono">{{ item.barcode }}</td>
                <td>
                  <span class="badge" :class="`badge-${toneOf(ITEM_STATUS, item.status)}`">
                    {{ ITEM_STATUS[item.status]?.label || item.status }}
                  </span>
                </td>
                <td>{{ item.location || '-' }}</td>
                <td>
                  <button
                    v-if="item.status !== 'BORROWED'"
                    class="btn btn-sm btn-danger"
                    :disabled="busyId === `item-${item.item_id}`"
                    @click="onRemoveItem(item)"
                  >
                    删除
                  </button>
                  <span v-else class="book-meta">在借中</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </AppModal>
  </div>
</template>
