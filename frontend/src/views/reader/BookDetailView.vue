<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { catalogApi, reservationApi, reviewApi } from '../../api'
import StateBlock from '../../components/StateBlock.vue'
import { ITEM_STATUS, itemTypeLabel, toneOf } from '../../constants'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../composables/useToast'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const toast = useToast()

const titleId = Number(route.params.titleId)

const detail = ref(null)
const reviews = ref([])
const averageRating = ref(0)
const loading = ref(true)
const reserving = ref(false)
const submittingReview = ref(false)

const reviewForm = reactive({ rating: 5, comment: '' })
const hoverRating = ref(0)

const availableCount = computed(
  () => detail.value?.items?.filter((i) => i.status === 'AVAILABLE').length || 0,
)

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await catalogApi.detail(titleId)
  } catch (err) {
    toast.error(err.message)
    detail.value = null
  } finally {
    loading.value = false
  }
}

async function loadReviews() {
  try {
    const data = await reviewApi.listByTitle(titleId)
    reviews.value = data.reviews || []
    averageRating.value = data.average_rating || 0
  } catch {
    reviews.value = []
  }
}

async function onReserve() {
  reserving.value = true
  try {
    await reservationApi.create(titleId)
    toast.success('预约成功，请留意到馆通知')
    await loadDetail()
  } catch (err) {
    toast.error(err.message)
  } finally {
    reserving.value = false
  }
}

async function onSubmitReview() {
  if (!reviewForm.rating) {
    toast.error('请先选择评分')
    return
  }
  submittingReview.value = true
  try {
    await reviewApi.submit({
      title_id: titleId,
      rating: reviewForm.rating,
      comment: reviewForm.comment.trim() || null,
    })
    toast.success('评论已提交，待管理员审核通过后公开展示')
    reviewForm.comment = ''
    reviewForm.rating = 5
    await loadReviews()
  } catch (err) {
    toast.error(err.message)
  } finally {
    submittingReview.value = false
  }
}

function starsText(value) {
  const full = Math.round(Number(value) || 0)
  return '★'.repeat(full) + '☆'.repeat(Math.max(0, 5 - full))
}

onMounted(async () => {
  await loadDetail()
  await loadReviews()
})
</script>

<template>
  <div class="content-narrow">
    <button class="btn btn-sm" style="margin-bottom: 14px" @click="router.back()">← 返回</button>

    <StateBlock :loading="loading" :empty="!loading && !detail" empty-text="图书不存在">
      <div v-if="detail" class="card">
        <div class="card-head">
          <div>
            <h2>{{ detail.title }}</h2>
            <p>{{ detail.author }}</p>
          </div>
          <div style="text-align: right">
            <div class="stars" style="font-size: 18px">{{ starsText(averageRating) }}</div>
            <div class="book-meta">
              {{ averageRating || 0 }} 分 · {{ detail.review_count }} 条已公开评论
            </div>
          </div>
        </div>

        <div class="stat-row" style="margin-bottom: 4px">
          <div class="stat">
            <div class="stat-value">{{ availableCount }}</div>
            <div class="stat-label">可借副本</div>
          </div>
          <div class="stat">
            <div class="stat-value">{{ detail.items.length }}</div>
            <div class="stat-label">馆藏总量</div>
          </div>
          <div class="stat">
            <div class="stat-value" style="font-size: 15px; padding-top: 6px">
              {{ itemTypeLabel(detail.item_type) }}
            </div>
            <div class="stat-label">出借物类型</div>
          </div>
          <div class="stat">
            <div class="stat-value" style="font-size: 15px; padding-top: 6px">
              {{ detail.price ?? '-' }}
            </div>
            <div class="stat-label">定价</div>
          </div>
        </div>

        <div class="grid grid-3" style="margin-top: 12px">
          <div class="book-meta">ISBN：<span class="mono">{{ detail.isbn }}</span></div>
          <div class="book-meta">出版社：{{ detail.publisher || '-' }}</div>
          <div class="book-meta">出版年：{{ detail.published_year || '-' }}</div>
          <div class="book-meta">分类：{{ detail.category || '-' }}</div>
        </div>
      </div>

      <div v-if="detail" class="card">
        <div class="card-head">
          <div>
            <h3>馆藏副本</h3>
            <p>条码为借还办理时使用的馆藏标识</p>
          </div>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>条码</th>
                <th>状态</th>
                <th>馆藏位置</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in detail.items" :key="item.item_id">
                <td class="mono">{{ item.barcode }}</td>
                <td>
                  <span class="badge" :class="`badge-${toneOf(ITEM_STATUS, item.status)}`">
                    {{ ITEM_STATUS[item.status]?.label || item.status }}
                  </span>
                </td>
                <td>{{ item.location || '-' }}</td>
              </tr>
              <tr v-if="detail.items.length === 0">
                <td colspan="3" style="text-align: center; color: var(--text-faint)">
                  暂无馆藏副本
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="auth.isReader.value" style="margin-top: 14px">
          <button class="btn btn-primary" :disabled="reserving" @click="onReserve">
            {{ reserving ? '提交中…' : '预约这本书' }}
          </button>
          <span class="book-meta" style="margin-left: 10px">
            预约后进入排队序列，到馆后可到柜台办理借阅
          </span>
        </div>
      </div>

      <div v-if="detail" class="card">
        <div class="card-head">
          <div>
            <h3>读者评论</h3>
            <p>评论需经管理员审核后公开；评分范围 1–5 分</p>
          </div>
        </div>

        <form v-if="auth.isReader.value" class="card" style="background: var(--surface-2)" @submit.prevent="onSubmitReview">
          <div class="field">
            <label>我的评分</label>
            <div class="stars-input">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                :class="{ on: n <= (hoverRating || reviewForm.rating) }"
                @mouseenter="hoverRating = n"
                @mouseleave="hoverRating = 0"
                @click="reviewForm.rating = n"
              >
                ★
              </button>
              <span class="book-meta" style="align-self: center; margin-left: 8px">
                {{ reviewForm.rating }} 分
              </span>
            </div>
          </div>
          <div class="field">
            <label for="comment">评论内容</label>
            <textarea
              id="comment"
              v-model="reviewForm.comment"
              class="textarea"
              placeholder="说说这本书的阅读体验（可留空，仅评分）"
            />
          </div>
          <button class="btn btn-primary" type="submit" :disabled="submittingReview">
            {{ submittingReview ? '提交中…' : '提交评论' }}
          </button>
        </form>

        <div v-else class="alert alert-info" style="margin-top: 10px">
          仅读者账号可发表评论，当前身份为{{ auth.role.value === 'admin' ? '系统管理员' : '图书管理员' }}。
        </div>

        <StateBlock :empty="reviews.length === 0" empty-text="还没有公开的评论" empty-icon="💬">
          <div
            v-for="review in reviews"
            :key="review.review_id"
            style="
              padding: 12px 0;
              border-bottom: 1px solid var(--border);
            "
          >
            <div style="display: flex; justify-content: space-between; gap: 10px">
              <span class="stars">{{ starsText(review.rating) }}</span>
              <span class="book-meta">{{ review.created_at?.slice(0, 10) }}</span>
            </div>
            <div style="margin-top: 4px">{{ review.comment || '（仅评分，未填写文字）' }}</div>
          </div>
        </StateBlock>
      </div>
    </StateBlock>
  </div>
</template>
