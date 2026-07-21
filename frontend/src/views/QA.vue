<template>
  <div class="qa-page">
    <!-- 背景装饰 -->
    <div class="bg-decorations">
      <div class="circle c1"></div>
      <div class="circle c2"></div>
      <div class="circle c3"></div>
    </div>

    <div class="qa-container">
      <!-- 顶部标题栏 -->
      <div class="qa-header">
        <div class="header-left">
          <span class="header-icon">🤖</span>
          <div class="header-text">
            <h2>旅游知识问答</h2>
            <span class="header-subtitle">基于 RAG 智能检索，为您解答旅游相关问题</span>
          </div>
        </div>
        <div class="header-actions">
          <a-tooltip title="清空对话">
            <a-button
              class="clear-btn"
              :disabled="messages.length === 0 || isStreaming"
              @click="handleClear"
            >
              🗑️ 清空
            </a-button>
          </a-tooltip>
          <a-tooltip title="返回首页">
            <a-button class="back-btn" @click="router.push('/')">
              🏠 首页
            </a-button>
          </a-tooltip>
        </div>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-area" ref="chatAreaRef">
        <!-- 空状态 - 推荐问题 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <h3>有什么旅游问题尽管问我！</h3>
          <p>我可以帮您查询景点信息、旅游攻略、天气情况等</p>
          <div class="suggested-questions">
            <div
              v-for="(q, i) in suggestedQuestions"
              :key="i"
              class="suggested-item"
              @click="handleSuggestedQuestion(q)"
            >
              <span class="suggested-icon">{{ suggestedIcons[i] }}</span>
              <span>{{ q }}</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message-wrapper', msg.role]"
          >
            <div class="message-avatar">
              <span v-if="msg.role === 'user'">👤</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-bubble">
              <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
              <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
          </div>

          <!-- 流式加载指示器 -->
          <div v-if="isStreaming && !currentStreamingContent" class="message-wrapper assistant">
            <div class="message-avatar"><span>🤖</span></div>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <a-textarea
            ref="textareaRef"
            v-model:value="inputValue"
            :placeholder="isStreaming ? '正在回答中...' : '输入您的旅游问题，按 Enter 发送...'"
            :disabled="isStreaming"
            :auto-size="{ minRows: 1, maxRows: 4 }"
            @keydown="handleKeydown"
            class="chat-input"
          />
          <a-button
            type="primary"
            class="send-btn"
            :loading="isStreaming"
            :disabled="!inputValue.trim() || isStreaming"
            @click="handleSend"
          >
            <span v-if="!isStreaming">发送 🚀</span>
            <span v-else>回答中...</span>
          </a-button>
        </div>
        <div class="input-hint">
          基于 Pinecone 向量检索 + MongoDB 多轮对话记忆 | 按 Enter 发送，Shift+Enter 换行
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { marked } from 'marked'
import { createQAStream, clearQASession } from '@/services/api'
import type { ChatMessage } from '@/types'

const router = useRouter()

// 状态
const messages = ref<ChatMessage[]>([])
const inputValue = ref('')
const isStreaming = ref(false)
const currentStreamingContent = ref('')
const sessionId = ref<string | undefined>(undefined)
const chatAreaRef = ref<HTMLElement | null>(null)
const textareaRef = ref<any>(null)
let abortController: AbortController | null = null

// 推荐问题
const suggestedQuestions = [
  '故宫门票多少钱？需要提前预约吗？',
  '北京三天两夜怎么安排行程？',
  '去西安旅游有什么必吃的美食？',
  '三亚什么时候去最合适？'
]
const suggestedIcons = ['🏯', '📅', '🍜', '🏖️']

// 生成唯一 ID
function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

// 格式化时间
function formatTime(ts: number): string {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// Markdown 渲染（使用 marked 库）
function renderMarkdown(text: string): string {
  return marked.parse(text, { breaks: true }) as string
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

// 发送消息
function handleSend() {
  const question = inputValue.value.trim()
  if (!question || isStreaming.value) return

  // 添加用户消息
  messages.value.push({
    id: genId(),
    role: 'user',
    content: question,
    timestamp: Date.now()
  })
  inputValue.value = ''
  nextTick(() => {
    inputValue.value = ''
    const el = textareaRef.value?.$el?.querySelector('textarea') || textareaRef.value?.$el
    if (el) el.value = ''
  })
  isStreaming.value = true
  currentStreamingContent.value = ''
  scrollToBottom()

  // 创建助手消息占位
  const assistantMsg: ChatMessage = {
    id: genId(),
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    isStreaming: true
  }
  messages.value.push(assistantMsg)
  scrollToBottom()

  // 发起 SSE 流式请求
  abortController = createQAStream(
    question,
    sessionId.value,
    // onToken
    (content) => {
      currentStreamingContent.value += content
      assistantMsg.content = currentStreamingContent.value
      scrollToBottom()
    },
    // onDone
    (data) => {
      assistantMsg.content = data.answer
      assistantMsg.isStreaming = false
      assistantMsg.timestamp = Date.now()
      sessionId.value = data.session_id
      isStreaming.value = false
      currentStreamingContent.value = ''
      abortController = null
      scrollToBottom()
    },
    // onError
    (error) => {
      assistantMsg.content = `❌ 抱歉，出现了错误：${error}`
      assistantMsg.isStreaming = false
      isStreaming.value = false
      currentStreamingContent.value = ''
      abortController = null
      message.error('问答请求失败: ' + error)
    }
  )
}

// 处理推荐问题点击
function handleSuggestedQuestion(q: string) {
  inputValue.value = q
  handleSend()
}

// 键盘事件
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 清空对话
async function handleClear() {
  if (sessionId.value) {
    try {
      await clearQASession(sessionId.value)
    } catch {
      // 忽略错误，前端仍然清空
    }
  }
  messages.value = []
  sessionId.value = undefined
  message.success('对话已清空')
}

// 组件卸载时中断请求
onBeforeUnmount(() => {
  abortController?.abort()
})
</script>

<style scoped>
.qa-page {
  min-height: calc(100vh - 134px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.bg-decorations {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}
.c1 {
  width: 300px; height: 300px;
  background: #667eea;
  top: -50px; right: -80px;
  animation: float 8s ease-in-out infinite;
}
.c2 {
  width: 200px; height: 200px;
  background: #764ba2;
  bottom: 10%; left: -60px;
  animation: float 10s ease-in-out infinite reverse;
}
.c3 {
  width: 150px; height: 150px;
  background: #667eea;
  top: 40%; right: 5%;
  animation: float 12s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

/* 主容器 */
.qa-container {
  width: 100%;
  max-width: 900px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  min-height: 500px;
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.6s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 顶部标题栏 */
.qa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px 20px 0 0;
  color: #fff;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  font-size: 32px;
}
.header-text h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.header-subtitle {
  font-size: 12px;
  opacity: 0.85;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.clear-btn, .back-btn {
  border-radius: 20px;
  font-size: 13px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(4px);
}
.clear-btn:hover:not(:disabled), .back-btn:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  border-color: rgba(255, 255, 255, 0.6) !important;
  color: #fff !important;
}
.clear-btn:disabled {
  opacity: 0.4;
  color: rgba(255, 255, 255, 0.6);
}

/* 聊天区域 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}
.chat-area::-webkit-scrollbar {
  width: 6px;
}
.chat-area::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 3px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  animation: fadeIn 0.8s ease;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  animation: bounce 2s ease infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.empty-state h3 {
  font-size: 22px;
  color: #333;
  margin-bottom: 8px;
}
.empty-state p {
  color: #888;
  font-size: 14px;
  margin-bottom: 28px;
}
.suggested-questions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  max-width: 560px;
}
.suggested-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: #f8f9fc;
  border: 1px solid #e8ecf1;
  border-radius: 14px;
  cursor: pointer;
  font-size: 14px;
  color: #444;
  transition: all 0.25s ease;
}
.suggested-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
}
.suggested-icon {
  font-size: 22px;
  flex-shrink: 0;
}

/* 消息列表 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 85%;
  animation: msgIn 0.35s ease;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-wrapper.assistant {
  align-self: flex-start;
}
.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.message-wrapper.user .message-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.message-wrapper.assistant .message-avatar {
  background: #f0f2f5;
}
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.7;
  font-size: 14px;
  position: relative;
}
.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message-wrapper.assistant .message-bubble {
  background: #f4f6f9;
  color: #333;
  border-bottom-left-radius: 4px;
}
.message-content {
  word-break: break-word;
}
.message-content :deep(strong) {
  font-weight: 600;
}
.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SFMono-Regular', Consolas, monospace;
}
.message-wrapper.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

/* Markdown 标题 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 12px 0 8px;
  font-weight: 600;
}
.message-content :deep(h1) { font-size: 18px; }
.message-content :deep(h2) { font-size: 16px; }
.message-content :deep(h3) { font-size: 15px; }

/* Markdown 列表 */
.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}
.message-content :deep(li) {
  margin: 4px 0;
}

/* Markdown 代码块 */
.message-content :deep(pre) {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}
.message-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 13px;
}

/* Markdown 引用 */
.message-content :deep(blockquote) {
  border-left: 3px solid #667eea;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

/* Markdown 表格 */
.message-content :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 12px;
  text-align: left;
}
.message-content :deep(th) {
  background: #f0f2f5;
}
.message-time {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.5;
  text-align: right;
}
.message-wrapper.assistant .message-time {
  text-align: left;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a0a0a0;
  animation: typing 1.4s infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* 输入区域 */
.input-area {
  padding: 16px 24px 20px;
  border-top: 1px solid #eef0f4;
  flex-shrink: 0;
  background: #fff;
  border-radius: 0 0 20px 20px;
}
.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.chat-input {
  flex: 1;
  border-radius: 14px !important;
  border: 2px solid #e8ecf1;
  padding: 10px 16px;
  font-size: 14px;
  resize: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.chat-input:focus, .chat-input:hover {
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}
.chat-input:disabled {
  background: #f8f9fc;
}
.send-btn {
  height: 44px;
  border-radius: 14px !important;
  padding: 0 24px;
  font-size: 14px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
}
.send-btn:disabled {
  opacity: 0.5;
}
.input-hint {
  text-align: center;
  font-size: 11px;
  color: #aaa;
  margin-top: 10px;
}

/* 响应式 */
@media (max-width: 768px) {
  .qa-page {
    padding: 12px;
  }
  .qa-container {
    height: calc(100vh - 100px);
    border-radius: 16px;
  }
  .qa-header {
    padding: 12px 16px;
    border-radius: 16px 16px 0 0;
  }
  .header-icon { font-size: 26px; }
  .header-text h2 { font-size: 16px; }
  .header-subtitle { display: none; }
  .suggested-questions {
    grid-template-columns: 1fr;
  }
  .chat-area {
    padding: 16px;
  }
  .input-area {
    padding: 12px 16px 16px;
    border-radius: 0 0 16px 16px;
  }
  .send-btn {
    padding: 0 16px;
  }
}
</style>
