import axios from 'axios'
import type { TripFormData, TripPlanResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

/**
 * 生成旅行计划
 */
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    console.error('生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  }
}

/**
 * RAG 问答 - SSE 流式请求
 * 由于 EventSource 仅支持 GET，这里用 fetch + ReadableStream 解析 SSE
 */
export function createQAStream(
  question: string,
  sessionId: string | undefined,
  onToken: (content: string) => void,
  onDone: (data: { answer: string; question: string; session_id: string }) => void,
  onError: (error: string) => void
): AbortController {
  const controller = new AbortController()
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  ;(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/qa/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, session_id: sessionId }),
        signal: controller.signal
      })

      if (!response.ok) {
        onError(`请求失败: ${response.status}`)
        return
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 最后一行可能不完整，留在 buffer

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              if (currentEvent === 'token') {
                onToken(parsed.content)
              } else if (currentEvent === 'done') {
                onDone(parsed)
              } else if (currentEvent === 'error') {
                onError(parsed.error)
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onError(err.message || '网络错误')
      }
    }
  })()

  return controller
}

/**
 * RAG 健康检查
 */
export async function checkQAHealth(): Promise<any> {
  try {
    const response = await apiClient.get('/api/qa/health')
    return response.data
  } catch (error: any) {
    console.error('RAG 健康检查失败:', error)
    throw new Error(error.message || 'RAG 健康检查失败')
  }
}

/**
 * 清空会话历史
 */
export async function clearQASession(sessionId: string): Promise<any> {
  try {
    const response = await apiClient.delete(`/api/qa/session/${sessionId}`)
    return response.data
  } catch (error: any) {
    console.error('清空会话失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '清空会话失败')
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient

