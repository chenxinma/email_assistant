# 配置说明

## 环境配置

### 环境变量
- `CONFIG_FILE`: 配置文件路径（默认值: `data/config.json`）
- `DB_FILE`: 数据库文件路径（默认值: `data/email_assistant.db`）
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry 端点（如配置的话）

## 配置文件结构 (data/config.json)

应用使用 `data/config.json` 文件进行配置，包含以下结构：

### 邮件配置 (mail)
```json
{
  "mail": {
    "refreshInterval": 15,
    "indexedFolders": ["INBOX"],
    "emailAddress": "your_email@example.com",
    "emailPassword": "your_email_password", 
    "imapServer": "imap.example.com",
    "imapPort": 993,
    "smtpServer": "smtp.example.com",
    "smtpPort": 465
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `refreshInterval` | 整数 | 邮件刷新间隔时间（分钟） |
| `indexedFolders` | 字符串数组 | 需要同步的邮件文件夹列表 |
| `emailAddress` | 字符串 | 邮箱地址 |
| `emailPassword` | 字符串 | 邮箱登录密码或授权码 |
| `imapServer` | 字符串 | IMAP服务器地址 |
| `imapPort` | 整数 | IMAP服务器端口（默认993） |
| `smtpServer` | 字符串 | SMTP服务器地址（暂未使用） |
| `smtpPort` | 整数 | SMTP服务器端口（暂未使用） |

### 人工智能配置 (ai)

```json
{
  "ai": {
    "embeddingModel": "bge-large-zh-v1.5",
    "embeddingBaseUrl": "http://localhost:9997/v1",
    "embeddingApiKey": "empty password",
    "summaryModel": "qwen3-max",
    "qaModel": "qwen3-max", 
    "summaryLength": 512,
    "whoami": "我是谁？"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `embeddingModel` | 字符串 | 邮件向量化使用的嵌入模型 |
| `embeddingBaseUrl` | 字符串 | 嵌入模型API的基础URL |
| `embeddingApiKey` | 字符串 | 嵌入模型API密钥 |
| `summaryModel` | 字符串 | 摘要生成使用的模型 |
| `qaModel` | 字符串 | 问答功能使用的模型 |
| `summaryLength` | 整数 | 摘要生成的最大长度（字符数） |
| `whoami` | 字符串 | 用户标识信息 |

## 初始化数据库

首次运行应用前需要初始化数据库，请使用以下命令：

```bash
uv run email-assistant --init
```

这将创建必要的数据库表结构。

## OTEL 监控配置

如果在配置中设置了 `otel_endpoint`，系统将启用 OpenTelemetry 监控，默认发送到 `http://localhost:4318` 端点，用于收集日志、追踪请求等。