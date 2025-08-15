import axios from 'axios'

// 创建axios实例
// 创建基础axios实例（非流式）
const api = axios.create({
  baseURL: '/api', // 使用相对路径，通过vite代理转发到后端
  timeout: 30000, // 设置为30秒
  headers: {
    'Content-Type': 'application/json',
  },
})

// 浏览器环境不支持responseType: 'stream'，使用fetch API处理流式响应
// 删除axios流式实例创建

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // 服务器响应了错误状态码
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('Network Error:', error.request)
    } else {
      // 其他错误
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// API接口定义
export const apiService = {
  // 获取每日摘要
  getDailySummary: () => api.get('/summary/daily'),
  
  // 搜索邮件
  searchEmails: (query) => api.post('/emails/search', query),
  
  // 获取模板
  getTemplates: () => api.get('/templates'),
  
  // 发送邮件
  sendEmail: (email) => api.post('/emails/send', email),
  
  // 获取配置
  getConfig: () => api.get('/config'),
  
  // 获取邮件列表
  getEmails: (params) => api.get('/emails', { params }),

  // 刷新邮件（流式响应）
  refreshEmails: async (days, onMessage, onComplete, onError) => {
    try {
      const response = await fetch('/api/emails/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            if (onComplete) onComplete();
            return;
          }

          const chunk = decoder.decode(value, { stream: true });
          // 处理每个数据块
          const lines = chunk.split('\n');
          lines.forEach(line => {
            if (line.startsWith('data: ')) {
              const data = line.substring(6);
              if (data != '[DONE]') {
                try {
                  const jsonData = JSON.parse(data);
                  if (onMessage) onMessage(jsonData);
                } catch (error) {
                  console.error('解析流式数据失败:', error);
                  if (onError) onError(error);
                }
              }
            }
          });

          read();
        }).catch(error => {
          console.error('读取流式数据失败:', error);
          if (onError) onError(error);
        });
      }

      read();
      return response;
    } catch (error) {
      console.error('请求失败:', error);
      if (onError) onError(error);
      throw error;
    }
  },
}

export default api