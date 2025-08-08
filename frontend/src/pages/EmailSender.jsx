import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Select, Card, Typography, message, Space } from 'antd'
import { SendOutlined, PlusOutlined } from '@ant-design/icons'
import { apiService } from '../services/api'

const { Title, Text } = Typography
const { Option } = Select

const EmailSender = () => {
  const [form] = Form.useForm()
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const response = await apiService.getTemplates()
      setTemplates(response.data || [])
    } catch (error) {
      message.error('获取模板失败: ' + error.message)
    }
  }

  const handleTemplateChange = (templateId) => {
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setSelectedTemplate(template)
      form.setFieldsValue({
        subject: template.subject,
        content: template.content
      })
    }
  }

  const handleSendEmail = async (values) => {
    try {
      const emailData = {
        subject: values.subject,
        content: values.content,
        recipient: values.recipient,
        sender: '', // 这将在后端根据账户配置填充
        date: new Date().toISOString(),
        folder: 'SENT'
      }
      
      const response = await apiService.sendEmail(emailData)
      message.success(response.data.message || '邮件发送成功')
      form.resetFields()
    } catch (error) {
      message.error('发送邮件失败: ' + error.message)
    }
  }

  return (
    <div>
      <Title level={2}>写邮件</Title>
      <Card title="选择模板">
        <Space>
          <Select
            style={{ width: 200 }}
            placeholder="选择邮件模板"
            onChange={handleTemplateChange}
          >
            {templates.map(template => (
              <Option key={template.id} value={template.id}>
                {template.name}
              </Option>
            ))}
          </Select>
          <Button type="primary" icon={<PlusOutlined />}>
            新建模板
          </Button>
        </Space>
      </Card>

      <Card title="邮件内容" style={{ marginTop: 20 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSendEmail}
        >
          <Form.Item
            name="recipient"
            label="收件人"
            rules={[{ required: true, message: '请输入收件人' }]}
          >
            <Input placeholder="请输入收件人邮箱，多个邮箱用逗号分隔" />
          </Form.Item>

          <Form.Item
            name="subject"
            label="主题"
            rules={[{ required: true, message: '请输入邮件主题' }]}
          >
            <Input placeholder="请输入邮件主题" />
          </Form.Item>

          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入邮件内容' }]}
          >
            <Input.TextArea
              rows={10}
              placeholder="请输入邮件内容，使用{keyword}语法标记替换字段"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SendOutlined />}>
              发送邮件
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default EmailSender