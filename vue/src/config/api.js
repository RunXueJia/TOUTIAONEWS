import axios from 'axios'

/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置：跟随页面主机名，避免 localhost 与 127.0.0.1 之间的跨站 Cookie 限制。
const apiHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'

export const apiConfig = {
  // 后端API基础URL
  baseURL: `http://${apiHost}:8000`,
}

const getCookie = (name) => {
  if (typeof document === 'undefined') return ''

  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : ''
}

axios.interceptors.request.use((config) => {
  if (config.url?.startsWith(apiConfig.baseURL)) {
    const token = getCookie('token')
    console.log('token',token);
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }

  return config
})

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  
  // API Key (由开发人员指定)
  apiKey: 'sk-9c4d89982a6a4bd3b7494d94751fe81c',
  
  // 使用的模型
  model: 'qwen3-max-preview'
}
