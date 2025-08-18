import React from 'react'
import '@ant-design/v5-patch-for-react-19';
import { Layout, Menu, theme, message, Button, Space } from 'antd'
import {
  MailOutlined,
  FileTextOutlined,
  SendOutlined,
  SettingOutlined,
  MinusOutlined,
  CloseOutlined,
  QuestionCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { apiService } from './services/api'
import './App.css'
import EmailSummary from './pages/EmailSummary'
import KnowledgeBase from './pages/KnowledgeBase'
import EmailSender from './pages/EmailSender'
import Settings from './pages/Settings'

const { Header, Content, Footer } = Layout

function App() {
  const [current, setCurrent] = React.useState('summary')
  const [refreshing, setRefreshing] = React.useState(false)
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()
  
  const handleRefresh = async () => {
    if (refreshing) {
      message.warning('邮件正在刷新中，请稍候...')
      return
    }
    
    setRefreshing(true)
    message.info('开始刷新邮件...')
    
    try {
      await apiService.refreshEmails(2,
        (data) => {
          if (data.count> 0) {
            message.info('收到邮件:' + data.title)
          } else {
            message.info('没有新的邮件了。')
          }
        },
        () => {
          message.success('邮件刷新完成')
          setRefreshing(false)
        },
        (error) => {
          message.error('刷新邮件失败: ' + error.message)
          setRefreshing(false)
        }
      )
    } catch (error) {
      message.error('刷新邮件失败: ' + error.message)
    } 
  }

  const items = [
    {
      key: 'summary',
      icon: <MailOutlined />,
      label: '邮件摘要',
    },
    {
      key: 'knowledge',
      icon: <FileTextOutlined />,
      label: '知识库',
    },
    {
      key: 'sender',
      icon: <SendOutlined />,
      label: '智能发送',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  const renderContent = () => {
    switch (current) {
      case 'summary':
        return <EmailSummary />
      case 'knowledge':
        return <KnowledgeBase />
      case 'sender':
        return <EmailSender />
      case 'settings':
        return <Settings />
      default:
        return <EmailSummary />
    }
  }

  return (
    <Layout className="dock-right">
      <Header className="app-header">
        <div className="header-left">
          <Space size="middle">
            <MailOutlined />
            <span className="app-title">邮件助手</span>
          </Space>
        </div>
        <div className="header-right">
          <Space size="middle">
            <Button type="text" icon={<MinusOutlined />} />
            <Button type="text" icon={<SettingOutlined />} onClick={() => setCurrent('settings')} />
            <Button type="text" icon={<CloseOutlined />} />
          </Space>
        </div>
      </Header>
      
      <Menu
        mode="horizontal"
        selectedKeys={[current]}
        onClick={(e) => setCurrent(e.key)}
        items={items}
        className="app-nav"
      />
      
      <Content className="app-content">
        <div className="content-wrapper">
          {renderContent()}
        </div>
      </Content>
      
      <Footer className="app-footer">
        <div className="footer-left">
          <Space size="middle">
            <span><button onClick={handleRefresh}>手动刷新</button></span>
          </Space>
        </div>
        <div className="footer-right">
          <Space size="middle">
            <Button type="text" icon={<QuestionCircleOutlined />} />
            <Button type="text" icon={<InfoCircleOutlined />} />
          </Space>
        </div>
      </Footer>
    </Layout>
  )
}

export default App