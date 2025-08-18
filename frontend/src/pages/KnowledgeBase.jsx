import React, { useState } from 'react'
import { apiService } from '../services/api'
import { message } from 'antd'

const KnowledgeBase = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState('上季度的市场推广预算是多少？')

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

  const handleAskQuestion = () => {
    if (!question.trim()) {
      message.warning('请输入问题')
      return
    }
    // 这里应该调用AI问答API
    message.success('问题已提交，正在获取答案...')
  }

  // 模拟相关邮件数据
  const relatedEmails = [
    {
      id: 1,
      subject: '关于2023年Q2季度市场推广预算的审批',
      sender: '李经理 <lijingli@company.com>',
      date: '2023-04-15',
      tags: ['预算', '市场推广', 'Q2']
    },
    {
      id: 2,
      subject: 'Q2市场推广活动效果分析报告',
      sender: '张三 <zhangsan@company.com>',
      date: '2023-07-02',
      tags: ['效果分析', '市场推广', '预算使用']
    }
  ]

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold">邮件知识库</h2>
      
      {/* 搜索区域 */}
      <div className="relative">
        <input 
          type="text" 
          placeholder="输入关键词搜索邮件内容..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          className="w-full py-3 px-4 pr-10 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all-300"
        />
        <button 
          onClick={handleSearch}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-primary transition-all-300"
        >
          <i className="fa fa-search text-lg"></i>
        </button>
      </div>
      
      {/* 搜索过滤选项 */}
      <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-100 flex flex-wrap gap-2">
        <button className="px-3 py-1 text-xs bg-primary/10 text-primary rounded-full">全部邮件</button>
        <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-full transition-all-300">收件箱</button>
        <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-full transition-all-300">已发送</button>
        <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-full transition-all-300">近1个月</button>
        <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-full transition-all-300">近3个月</button>
        <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-full transition-all-300">
          <i className="fa fa-filter mr-1"></i>更多筛选
        </button>
      </div>
      
      {/* 问答区域 */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 space-y-4">
        <h3 className="font-medium text-gray-800">智能问答</h3>
        
        <div className="space-y-4">
          {/* 示例问题 */}
          <div className="flex space-x-3">
            <div className="text-primary text-xl">
              <i className="fa fa-user-circle-o"></i>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg rounded-tl-none max-w-[85%]">
              <p className="text-sm">{question}</p>
            </div>
          </div>
          
          {/* 回答 */}
          <div className="flex space-x-3">
            <div className="text-accent text-xl">
              <i className="fa fa-robot"></i>
            </div>
            <div className="bg-accent/10 p-3 rounded-lg rounded-tl-none max-w-[85%]">
              <p className="text-sm text-gray-700">
                根据2023年Q2季度的邮件记录，上季度市场推广预算为150万元，其中线上推广占60%，线下活动占40%。相关审批邮件由财务部李经理于2023年4月15日发出。
              </p>
              <button className="text-accent text-xs mt-1 hover:underline">查看相关邮件</button>
            </div>
          </div>
        </div>
        
        {/* 提问框 */}
        <div className="border-t border-gray-100 pt-3">
          <div className="flex space-x-2">
            <input 
              type="text" 
              placeholder="请输入您的问题..." 
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
              className="flex-1 py-2 px-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary text-sm transition-all-300"
            />
            <button 
              onClick={handleAskQuestion}
              className="bg-primary text-white p-2 rounded-lg hover:bg-primary/90 transition-all-300"
            >
              <i className="fa fa-paper-plane-o"></i>
            </button>
          </div>
        </div>
      </div>
      
      {/* 相关邮件 */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 space-y-3">
        <h3 className="font-medium text-gray-800">相关邮件</h3>
        
        <div className="space-y-3">
          {relatedEmails.map(email => (
            <div 
              key={email.id} 
              className="p-2 border border-gray-100 rounded-lg hover:border-primary/30 hover:bg-primary/5 transition-all-300"
            >
              <div className="text-sm font-medium">{email.subject}</div>
              <div className="text-xs text-gray-500 mt-1">
                发件人：{email.sender} | 日期：{email.date}
              </div>
              <div className="mt-2 flex justify-between items-center">
                <div className="text-xs text-gray-600">
                  包含：{email.tags.join('、')}
                </div>
                <button className="text-primary text-xs hover:underline">查看详情</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default KnowledgeBase