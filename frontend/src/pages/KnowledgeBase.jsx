import React, { useState, useRef, useEffect } from 'react'
import { apiService } from '../services/api'
import { message, Input, Button, Card, Avatar, Space, Typography, Spin, Layout } from 'antd'
import { SendOutlined, UserOutlined, MessageOutlined, RightCircleFilled } from '@ant-design/icons'

const { Header, Content, Footer } = Layout;
const { Text } = Typography
const { TextArea } = Input

const ChatPage = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '您好！我是您的邮件助手。请问有什么我可以帮助您的吗？我可以帮您搜索邮件、总结内容等。',
      timestamp: new Date().toLocaleTimeString()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return

    // 添加用户消息到聊天记录
    const userMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    }
    setMessages(prevMessages => [...prevMessages, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      // 调用现有API进行搜索或问答
      const response = await apiService.searchEmails({
        query: inputValue,
        folder: 'INBOX'
      })
      
      const results = response.data.results || []
      
      // 生成助手回复
      let assistantContent = ''
      if (results.length > 0) {
        assistantContent = `我找到了 ${results.length} 封相关邮件。以下是主要信息：\n`
        
        // 从搜索结果中提取信息生成回答
        results.slice(0, 3).forEach((result, index) => {
          const subject = result.subject || '无主题'
          const sender = result.sender ? `来自 ${result.sender}` : ''
          const date = result.date ? `于 ${result.date}` : ''
          const snippet = result.content ? result.content.substring(0, 100) + '...' : '无内容'
          
          assistantContent += `\n${index + 1}. [${subject}] ${sender} ${date}\n   ${snippet}\n`
        })
        
        if (results.length > 3) {
          assistantContent += `\n还有 ${results.length - 3} 条结果未显示。您可以提供更具体的问题来获取更精准的信息。`
        }
      } else {
        assistantContent = '抱歉，我没有找到相关的邮件信息。请尝试使用不同的关键词再次搜索。'
      }
      
      // 添加助手回复到聊天记录
      const assistantMessage = {
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toLocaleTimeString()
      }
      
      setMessages(prevMessages => [...prevMessages, assistantMessage])
    } catch (error) {
      message.error(`抱歉，我暂时无法为您提供帮助: ${error.message || '未知错误'}`)
      console.error('获取邮件信息失败:', error)
      
      // 添加错误消息到聊天记录
      const errorMessage = {
        role: 'assistant',
        content: `抱歉，我暂时无法为您提供帮助。请稍后再试。`,
        timestamp: new Date().toLocaleTimeString()
      }
      
      setMessages(prevMessages => [...prevMessages, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className='flex flex-col h-full'>
      <div className='flex flex-1 overflow-y-auto scrollbar-thin' style={{paddingRight: 10, paddingLeft: 10, marginTop: 10}}>
        <div className="flex flex-col max-w-3xl mx-auto space-y-6">
          {messages.map((msg, index) => (
            <div 
              key={index} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <Avatar 
                  icon={msg.role === 'user' ? <UserOutlined /> : <MessageOutlined />} 
                  className={`mr-2 ${msg.role === 'user' ? 'ml-2 mr-0 bg-blue-100' : 'bg-green-100'}`}
                />
                <div>
                  <Card 
                    className={`p-3 ${msg.role === 'user' ? 'bg-blue-50' : 'bg-white'}`}
                    size="small"
                  >
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    <Text type="secondary" className="text-xs block mt-1">
                      {msg.timestamp}
                    </Text>
                  </Card>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex">
                <Avatar icon={<MessageOutlined />} className="mr-2 bg-green-100" />
                <Card 
                  className="p-3 bg-white" 
                  size="small"
                >
                  <div className="flex items-center">
                    <Spin size="small" className="mr-2" />
                    <span className="text-gray-500">正在思考...</span>
                  </div>
                </Card>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <div className='flex content-wrapper'>
        <Space.Compact className="w-full">
          <TextArea 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleKeyPress}
            placeholder="请输入您的问题... (Enter 发送, Shift+Enter 换行)"
            rows={3}
            autoSize={{ minRows: 3, maxRows: 6 }}
          />
          <Button 
            type="primary" 
            icon={<SendOutlined />} 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || loading}
          >
            发送
          </Button>
        </Space.Compact>
      </div>
    </div>
  )
}

export default ChatPage