import React from 'react'
import '@ant-design/v5-patch-for-react-19';
import { Layout, Menu, theme, message, Button } from 'antd'
import {
  MailOutlined,
  FileTextOutlined,
  SendOutlined,
  SettingOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { apiService } from './services/api'
import './App.css'
import EmailSummary from './pages/EmailSummary'
import KnowledgeBase from './pages/KnowledgeBase'
import EmailSender from './pages/EmailSender'
import Settings from './pages/Settings'

const { Header, Content, Sider } = Layout

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
      label: '今日摘要',
    },
    {
      key: 'knowledge',
      icon: <FileTextOutlined />,
      label: '邮件库',
    },
    {
      key: 'sender',
      icon: <SendOutlined />,
      label: '写邮件',
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
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="header">
        <div className="logo">邮件助手</div>
        <div style={{ marginLeft: 'auto' }}>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={handleRefresh}
            loading={refreshing}
            style={{ marginRight: 16 }}
          >
            刷新邮件
          </Button>
        </div>
      </Header>
      <Layout>
        <Sider width={200}>
          <Menu
            mode="inline"
            selectedKeys={[current]}
            onSelect={(e) => setCurrent(e.key)}
            items={items}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App