import React, { useState, useEffect } from 'react'
import { Card, Typography, Spin, message, Button, Space, Checkbox, Row, Col } from 'antd'
import { ReloadOutlined, CalendarOutlined, PlusOutlined } from '@ant-design/icons'
import { apiService } from '../services/api'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text } = Typography

const EmailSummary = () => {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState(null)

  useEffect(() => {
    fetchDailySummary()
  }, [])

  const fetchDailySummary = async () => {
    setLoading(true)
    try {
      const response = await apiService.getDailySummary()
      setSummary(response.data)
    } catch (error) {
      message.error('获取每日摘要失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="email-summary">
      {/* 日期和摘要控制 */}
      <div className="flex justify-between items-center mb-4">
        <Title level={4} className="mb-0">今日邮件摘要</Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchDailySummary}
            loading={loading}
            size="small"
          >
            刷新
          </Button>
        </Space>
      </div>
      {/* 邮件统计卡片 */}
      {/* 邮件摘要内容 */}
      <Card size="small" className="mb-4">
        {loading ? (
          <div className="text-center py-4">
            <Spin />
          </div>
        ) : summary ? (    
          <div>        
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
                }}>{summary.summary}</ReactMarkdown>
          </div>
        ) : (
          <Text type="secondary">暂无数据</Text>
        )}
      </Card>

      {/* 待办任务清单 */}

      {/* 重要邮件列表 */}
    </div>
  )
}

export default EmailSummary