import React, { useState, useRef, useEffect } from 'react'
import { apiService } from '../services/api'
import ReactMarkdown from 'react-markdown'
import { message, Input, Button, Card, Avatar, Space, Typography, Spin, Flex } from 'antd'
import { SendOutlined, UserOutlined, MessageOutlined, RightCircleFilled } from '@ant-design/icons'

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
  const assistantMessageRef = useRef(null)

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
    
    // 创建助手消息对象并保存引用
    const assistantMessage = {
      role: 'assistant',
      content: '', // 初始为空字符串
      timestamp: new Date().toLocaleTimeString()
    }
    
    // 保存助手消息的引用
    assistantMessageRef.current = assistantMessage
    
    // 将助手消息添加到消息列表
    setMessages(prevMessages => [...prevMessages, assistantMessage])
    
    // 调用现有API进行搜索或问答
    await apiService.searchEmails({
      query: inputValue,
      folder: 'INBOX'
    }, (data) => {
      // 获取流式数据并更新消息内容
      if (assistantMessageRef.current) {
        // 直接更新当前消息内容
        assistantMessageRef.current.content = data.content
        // 触发重新渲染
        setMessages(prevMessages => [...prevMessages])
      }
    }, () => {
      console.log(assistantMessage.content)
      // 请求完成，清除loading状态和引用
      setLoading(false)
      assistantMessageRef.current = null
    }, (error) => {
      message.error(`抱歉，我暂时无法为您提供帮助: ${error.message || '未知错误'}`)
      console.error('获取邮件信息失败:', error)

      if (assistantMessageRef.current) {
        assistantMessageRef.current.content = `抱歉，我暂时无法为您提供帮助。请稍后再试。`
        assistantMessageRef.current.timestamp = new Date().toLocaleTimeString()
        setMessages(prevMessages => [...prevMessages])
      }
      
      setLoading(false)
      assistantMessageRef.current = null
    })
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Flex vertical className='h-full'>
      <Flex className='overflow-y-auto scrollbar-thin h-full' >
        <Flex vertical gap="small" className='content-wrapper' >
          {messages.map((msg, index) => (
            <Flex  
              key={index} 
              justify={msg.role === 'user' ? 'flex-end' : 'flex-start'}
            >
              <Card 
                className={`p-3 ${msg.role === 'user' ? 'bg-blue-50' : 'bg-white'}`}
                size="small"
              >
                <Flex justify={msg.role === 'user' ? 'flex-end' : 'flex-start'}>
                  <Avatar 
                    icon={msg.role === 'user' ? <UserOutlined /> : <MessageOutlined />} 
                    className={`${msg.role === 'user' ? 'bg-blue-100' : 'bg-green-100'}`}
                  />
                </Flex>
                <ReactMarkdown
                    components={{
                        code({node, inline, className, children, ...props}) {
                          const match = /language-(\w+)/.exec(className || '');
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={materialLight}
                              language={match[1]}
                              PreTag="div"
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}>{msg.content}
                </ReactMarkdown>
                {loading && msg.content ==='' && (
                    <Flex justify='center'>
                      <Spin size="small" className="mr-2" />
                      <span className="text-gray-500">正在生成回复...</span>
                    </Flex>)}
                <Text type="secondary" className="text-xs block mt-1">
                  {msg.timestamp}
                </Text>
              </Card>
            </Flex>
          ))}
          <div ref={messagesEndRef} />
        </Flex>
      </Flex>
      <Flex vertical={false} className='content-wrapper'>
        <TextArea 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onPressEnter={handleKeyPress}
          placeholder="请输入您的问题... (Enter 发送, Shift+Enter 换行)"
          autoSize={{ minRows: 2, maxRows: 3 }}
        />
        <Button 
          type={"primary"}
          icon={<SendOutlined />} 
          size="large"
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || loading}
          style={{ height: 54 }} 
        >
          发送
        </Button>
      </Flex>
    </Flex>
  )
}

export default ChatPage