import React from 'react'
import { Layout, Menu, theme } from 'antd'
import {
  MailOutlined,
  FileTextOutlined,
  SendOutlined,
  SettingOutlined
} from '@ant-design/icons'
import './App.css'
import EmailSummary from './pages/EmailSummary'
import KnowledgeBase from './pages/KnowledgeBase'
import EmailSender from './pages/EmailSender'
import Settings from './pages/Settings'

const { Header, Content, Sider } = Layout

function App() {
  const [current, setCurrent] = React.useState('summary')
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const items = [
    {
      key: 'summary',
      icon: <MailOutlined />,
      label: '今日摘要',
    },
    {
      key: 'knowledge',
      icon: <FileTextOutlined />,
      label: '知识库',
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