import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Card, Typography, message, List, Space, Modal, Switch } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography

const Settings = () => {
  const [form] = Form.useForm()
  const [accounts, setAccounts] = useState([])
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)

  useEffect(() => {
    // 模拟从localStorage或API获取账户信息
    const savedAccounts = localStorage.getItem('emailAccounts')
    if (savedAccounts) {
      setAccounts(JSON.parse(savedAccounts))
    }
  }, [])

  const saveAccounts = (newAccounts) => {
    setAccounts(newAccounts)
    localStorage.setItem('emailAccounts', JSON.stringify(newAccounts))
  }

  const handleAddAccount = (values) => {
    const newAccount = {
      id: Date.now(),
      ...values
    }
    
    saveAccounts([...accounts, newAccount])
    form.resetFields()
    message.success('账户添加成功')
  }

  const handleEditAccount = (account) => {
    setEditingAccount(account)
    form.setFieldsValue(account)
    setIsModalVisible(true)
  }

  const handleUpdateAccount = (values) => {
    const updatedAccounts = accounts.map(account => 
      account.id === editingAccount.id 
        ? { ...account, ...values } 
        : account
    )
    
    saveAccounts(updatedAccounts)
    setIsModalVisible(false)
    setEditingAccount(null)
    form.resetFields()
    message.success('账户更新成功')
  }

  const handleDeleteAccount = (accountId) => {
    const updatedAccounts = accounts.filter(account => account.id !== accountId)
    saveAccounts(updatedAccounts)
    message.success('账户删除成功')
  }

  const handleModalOk = () => {
    form.validateFields()
      .then(values => {
        if (editingAccount) {
          handleUpdateAccount(values)
        } else {
          handleAddAccount(values)
        }
      })
      .catch(info => {
        console.log('Validate Failed:', info)
      })
  }

  const handleModalCancel = () => {
    setIsModalVisible(false)
    setEditingAccount(null)
    form.resetFields()
  }

  return (
    <div>
      <Title level={2}>设置</Title>
      
      <Card title="邮箱账户">
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={() => setIsModalVisible(true)}
          style={{ marginBottom: 16 }}
        >
          添加账户
        </Button>
        
        <List
          dataSource={accounts}
          renderItem={account => (
            <List.Item
              actions={[
                <Button 
                  type="link" 
                  icon={<EditOutlined />} 
                  onClick={() => handleEditAccount(account)}
                >
                  编辑
                </Button>,
                <Button 
                  type="link" 
                  danger 
                  icon={<DeleteOutlined />} 
                  onClick={() => handleDeleteAccount(account.id)}
                >
                  删除
                </Button>
              ]}
            >
              <List.Item.Meta
                title={account.email}
                description={
                  <div>
                    <Text>IMAP服务器: {account.imapServer}:{account.imapPort}</Text>
                    <br />
                    <Text>SMTP服务器: {account.smtpServer}:{account.smtpPort}</Text>
                    <br />
                    <Text>监控目录: {account.folders?.join(', ') || 'INBOX'}</Text>
                  </div>
                }
              />
              <div>
                <Switch 
                  checked={account.enabled} 
                  onChange={(checked) => {
                    const updatedAccounts = accounts.map(acc => 
                      acc.id === account.id 
                        ? { ...acc, enabled: checked } 
                        : acc
                    )
                    saveAccounts(updatedAccounts)
                  }}
                  checkedChildren="启用" 
                  unCheckedChildren="禁用" 
                />
              </div>
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title={editingAccount ? "编辑邮箱账户" : "添加邮箱账户"}
        visible={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          name="accountForm"
        >
          <Form.Item
            name="email"
            label="邮箱地址"
            rules={[{ required: true, message: '请输入邮箱地址' }]}
          >
            <Input placeholder="example@domain.com" />
          </Form.Item>

          <Form.Item
            name="password"
            label="授权码"
            rules={[{ required: true, message: '请输入授权码' }]}
          >
            <Input.Password placeholder="请输入邮箱授权码（非密码）" />
          </Form.Item>

          <Form.Item
            name="imapServer"
            label="IMAP服务器"
            rules={[{ required: true, message: '请输入IMAP服务器地址' }]}
          >
            <Input placeholder="imap.domain.com" />
          </Form.Item>

          <Form.Item
            name="imapPort"
            label="IMAP端口"
            rules={[{ required: true, message: '请输入IMAP端口' }]}
          >
            <Input placeholder="993" />
          </Form.Item>

          <Form.Item
            name="smtpServer"
            label="SMTP服务器"
            rules={[{ required: true, message: '请输入SMTP服务器地址' }]}
          >
            <Input placeholder="smtp.domain.com" />
          </Form.Item>

          <Form.Item
            name="smtpPort"
            label="SMTP端口"
            rules={[{ required: true, message: '请输入SMTP端口' }]}
          >
            <Input placeholder="465" />
          </Form.Item>

          <Form.Item
            name="folders"
            label="监控目录"
          >
            <Input placeholder="INBOX,Projects （多个目录用逗号分隔）" />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="启用账户"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Settings