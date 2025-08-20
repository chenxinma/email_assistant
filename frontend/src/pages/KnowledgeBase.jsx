import React, { useState } from 'react'
import { apiService } from '../services/api'
import { message, Form, Input, Button, Card, Spin } from 'antd'
import { SearchOutlined } from '@ant-design/icons'


const KnowledgeBase = () => {
  const [form] = Form.useForm()
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    try {
      const { searchQuery } = form.getFieldsValue('searchQuery')
      const response = await apiService.searchEmails({ query: searchQuery, folder: 'INBOX' })
      setSearchResults(response.data.results || [])
    } catch (error) {
      message.error(`搜索失败: ${error.message || '未知错误'}`)
      console.error('搜索邮件失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold">邮件库</h2>
      <Card title="邮件内容" style={{ marginTop: 20 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleSearch}
          className="flex items-center gap-2"
        >
          <Form.Item 
            label="" 
            name='searchQuery'
            rules={[{ required: true, message: '请输入搜索内容' }]} >
            <Input placeholder="请输入搜索内容" style={{ width: 280 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
              搜索
            </Button>
          </Form.Item>
        </Form>
      </Card>
      <Card size="small" className="mb-4">
        {loading ? (
          <div className="text-center py-4">
            <Spin />
          </div>
        ) : searchResults.length > 0 ? (    
          <div> 
            <h3 className="text-lg font-semibold mb-2">搜索结果 ({searchResults.length})</h3> 
            <div className="space-y-3"> 
              {searchResults.map((result) => (
                <Card key={result.id || result.uid} size="small" className="hover:shadow-md transition-shadow">
                  <div className="font-medium mb-1">{result.subject || '无主题'}</div>
                  <div className="text-sm text-gray-600 mb-1">
                    {result.sender ? `发件人: ${result.sender}` : ''}
                    {result.date ? ` · ${result.date}` : ''}
                  </div>
                  <div className="text-sm line-clamp-2 mt-1">{result.content || '无内容'}</div>
                </Card>
              ))} 
            </div> 
          </div>
        ) : (
          <div>
            <p>暂无搜索结果</p>
          </div>
        )}
      </Card>
    </div>
  )
}

export default KnowledgeBase