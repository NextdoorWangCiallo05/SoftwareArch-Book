<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { catalogApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { ITEM_TYPES, itemTypeLabel } from '../../constants'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'

const router = useRouter()
const auth = useAuth()
const toast = useToast()

const PAGE_SIZE = 12

const filters = reactive({ keyword: '', author: '', category: '', item_type: '' })
const page = ref(1)
const books = ref([])
const total = ref(0)
const loading = ref(false)
const searched = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function load() {
  loading.value = true
  try {
    const data = await catalogApi.search({
      keyword: filters.keyword.trim() || undefined,
      author: filters.author.trim() || undefined,
      category: filters.category.trim() || undefined,
      item_type: filters.item_type || undefined,
      page: page.value,
      page_size: PAGE_SIZE,
    })
    books.value = data.books || []
    total.value = data.total || 0
    searched.value = true
  } catch (err) {
    toast.error(err.message)
    books.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  filters.keyword = ''
  filters.author = ''
  filters.category = ''
  filters.item_type = ''
  page.value = 1
  load()
}

function goPage(delta) {
  const next = page.value + delta
  if (next < 1 || next > totalPages.value) return
  page.value = next
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="card">
      <div class="card-head">
        <div>
          <h3>馆藏检索</h3>
          <p>支持按书名关键词、作者、分类与出借物类型组合查询</p>
        </div>
      </div>

      <form class="inline-form" @submit.prevent="onSearch">
        <div class="field">
          <label for="kw">书名关键词</label>
          <input id="kw" v-model="filters.keyword" class="input" placeholder="如：算法" />
        </div>
        <div class="field">
          <label for="au">作者</label>
          <input id="au" v-model="filters.author" class="input" placeholder="如：Knuth" />
        </div>
        <div class="field">
          <label for="cat">分类</label>
          <input id="cat" v-model="filters.category" class="input" placeholder="如：计算机" />
        </div>
        <div class="field">
          <label for="it">类型</label>
          <select id="it" v-model="filters.item_type" class="select">
            <option value="">全部</option>
            <option v-for="t in ITEM_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <button class="btn btn-primary" type="submit">查询</button>
        <button class="btn" type="button" @click="onReset">重置</button>
      </form>
    </div>

    <div class="card">
      <div class="card-head">
        <div>
          <h3>检索结果</h3>
          <p>共 {{ total }} 条，第 {{ page }} / {{ totalPages }} 页</p>
        </div>
      </div>

      <StateBlock
        :loading="loading"
        :empty="!loading && books.length === 0"
        :empty-text="searched ? '没有符合条件的图书，换个关键词试试' : '请输入条件后查询'"
        empty-icon="🔍"
      >
        <div class="grid grid-books">
          <article v-for="book in books" :key="book.title_id" class="book-card">
            <div>
              <div class="book-title">{{ book.title }}</div>
              <div class="book-meta">{{ book.author }}</div>
            </div>
            <div class="book-meta">
              <div>ISBN：<span class="mono">{{ book.isbn }}</span></div>
              <div>
                {{ itemTypeLabel(book.item_type)
                }}<template v-if="book.category"> · {{ book.category }}</template>
              </div>
            </div>
            <div class="book-card-footer">
              <span
                class="badge"
                :class="book.available_count > 0 ? 'badge-success' : 'badge-warning'"
              >
                {{ book.available_count > 0 ? `可借 ${book.available_count} 册` : '暂无在馆副本' }}
              </span>
              <button class="btn btn-sm" @click="router.push(`/book/${book.title_id}`)">
                查看详情
              </button>
            </div>
          </article>
        </div>

        <div
          v-if="totalPages > 1"
          style="display: flex; justify-content: center; gap: 10px; margin-top: 18px"
        >
          <button class="btn btn-sm" :disabled="page <= 1" @click="goPage(-1)">上一页</button>
          <span class="book-meta" style="align-self: center">{{ page }} / {{ totalPages }}</span>
          <button class="btn btn-sm" :disabled="page >= totalPages" @click="goPage(1)">
            下一页
          </button>
        </div>
      </StateBlock>
    </div>

    <div v-if="auth.isReader.value" class="alert alert-info" style="margin-top: 16px">
      提示：借书与还书需到馆员柜台办理（借还均由图书管理员代理，符合业务规则）。你可以在线预约、续借与发表评论。
    </div>
  </div>
</template>
