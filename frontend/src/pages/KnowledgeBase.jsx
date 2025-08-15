import React, { useState } from 'react'
import { Input, Button, List, Card, Typography, message, Spin, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { apiService } from '../services/api'

const { Title, Text } = Typography

const KnowledgeBase = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索内容')
      return
    }

    setLoading(true)
    try {
      const response = await apiService.searchEmails({ query: searchQuery })
      setSearchResults(response.data.results || [])
    } catch (error) {
      message.error('搜索失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={2}>邮件库</Title>
      <Space.Compact style={{ marginBottom: 20, width: '100%' }}>
        <Input
          style={{ width: 'calc(100% - 100px)' }}
          placeholder="输入关键词或问题搜索邮件内容"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onPressEnter={handleSearch}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
          搜索
        </Button>
      </Space.Compact>

      {loading ? (
        <Spin size="large" />
      ) : (
        <List
          dataSource={searchResults}
          renderItem={(item) => (
            <List.Item>
              <Card style={{ width: '100%' }}>
                <Card.Meta
                  title={item.subject}
                  description={
                    <div>
                      <Text type="secondary">{item.sender} | {item.date}</Text>
                      <br />
                      <Text
                        ellipsis={{ symbol: '展开更多' }}
                        style={{ whiteSpace: 'pre-line' }}
                      >
                        {item.content.length > 500 ? item.content.substring(0, 500) + '...' : item.content}
                      </Text>
                      <br />
                      <Text type="secondary">差异: {(item.distance).toFixed(2)}</Text>
                    </div>
                  }
                />
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}

export default KnowledgeBase