import React, { useState, useEffect } from 'react'
import { Card, List, Typography, Spin, message } from 'antd'
import { apiService } from '../services/api'

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
    <div>
      <Title level={2}>今日摘要</Title>
      {loading ? (
        <Spin size="large" />
      ) : summary ? (
        <div>
          <Card title="摘要" style={{ marginBottom: 20 }}>
            <Text>{summary.summary}</Text>
          </Card>
          <Card title="待办事项">
            <List
              bordered
              dataSource={summary.tasks}
              renderItem={(item, index) => (
                <List.Item>
                  <Text>{index + 1}. {item}</Text>
                </List.Item>
              )}
            />
          </Card>
        </div>
      ) : (
        <Text>暂无数据</Text>
      )}
    </div>
  )
}

export default EmailSummary