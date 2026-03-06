# 邮件助手 API 接口文档

## 概述

邮件助手 API 是一个智能邮件管理系统接口，支持邮件智能搜索、摘要生成、邮件同步等功能。API 采用 FastAPI 框架构建，提供 RESTful 风格的接口。

**基础URL**: `http://0.0.0.0:9000`
**认证方式**: 通过配置文件中的邮箱凭据验证

## ag-ui 协议说明

邮件助手使用 ag_ui（Agent-User Interaction UI）协议实现智能代理与用户的交互。

### 简介
ag_ui 是专为 AI 代理与用户交互设计的统一接口协议，提供标准化的消息传递格式和交互模式。该协议支持：

- **多模态响应**: 支持文本、结构化数据、工具调用等多种返回格式
- **流式交互**: 使用 Server-Sent Events 实现实时响应流
- **工具集成**: 内置对多种工具的调用支持，包括异步工具
- **会话管理**: 支持上下文感知的连续对话

### 协议规范
- 响应格式遵循 SSE（Server-Sent Events）标准，流式传输结果到客户端
- 双向消息格式标准化，兼容多种前端 UI 组件
- 自动序列化复杂数据类型（日期、数组、对象）供前端使用
- 安全地传递异常信息以便调试

### 与邮件助手的集成
在邮件助手中，ag_ui 被用于：
- 自然语言邮件查询处理
- 邮件搜索和汇总功能
- 与向量数据库的交互
- AI辅助决策流程控制

当客户端通过 `/` 端点发出请求时，系统内部使用 ag_ui 协议解析查询、调度智能工具、并把结果流式返回给前端。

## API 响应格式

### ag-ui 响应协议 (POST /)
此端点使用 ag_ui 协议进行响应，根据请求的 Accept header 返回不同格式的内容。

**支持的 Accept 类型:**
- `text/plain`: 纯文本流式响应
- `application/json`: JSON 格式的响应
- `text/event-stream`: SSE 流式事件响应（默认）

### 邮件刷新响应格式 (POST /api/emails/refresh)
返回固定为 Server-Sent Events 格式的流式更新，用于显示处理进度。

## 端点详细说明

### 1. 邮件Agent交互

#### POST /

这是基于 ag_ui 实现的邮件智能助手交互端点，采用 Server-Sent Events (SSE) 流式传输协议实现服务端推送与客户端实时通信。

##### 请求头

- `Accept`: 指定响应内容类型，支持 `text/plain`, `application/json`, 或其他支持的格式（默认为 `text/plain`）
- `Content-Type`: `application/json`

##### 请求体

```json
{
  "query": "查询内容",
  "thread_id": "可选的线程ID",
  "messages": [],
  "model_extra": {},
  "tool_call_id": null
}
```

##### 响应

这是一个基于 ag_ui 的流式响应端点，按 SSE 协议持续推送消息给客户端，响应可能包括：

- **工具调用**: 在执行期间进行的各个邮件查询操作
- **工具结果**: 各个操作返回的数据
- **最终结果**: AI助手生成的最终答案
- **错误信息**: 如果在处理过程中出现问题

所有响应都遵循 Server-Sent Events 格式，使客户端能够实时接收并显示逐步的信息。

##### 示例

```bash
curl -X POST "http://0.0.0.0:9000/" \
  -H "Accept: text/plain" \
  -H "Content-Type: application/json" \
  -d '{"query": "今天收到的所有邮件摘要"}'
```

### 2. 邮件刷新

#### POST /api/emails/refresh

同步最新邮件到本地数据库，支持增量更新和邮件属性提取。

##### 查询参数

- `days`: 整数类型，表示要同步的近N天邮件（默认值: 2）

##### 响应格式

返回流式响应（Server-Sent Events），逐条推送邮件处理进度：

```json
{
  "message": "处理状态",
  "count": "处理计数(可选)",
  "title": "邮件标题(可选)"
}
```

可能的消息类型：
- `"文件夹处理中 INBOX"` - 开始处理特定文件夹
- `"邮件处理中"` - 正在处理邮件
- `"邮件处理失败"` - 处理失败的邮件
- `"邮件属性保存中"` - 正在保存邮件属性
- `"邮件刷新成功"` - 完成同步
- `"[DONE]"` - 处理完成

##### 示例

```bash
curl -X POST "http://0.0.0.0:9000/api/emails/refresh?days=7" \
  -H "Content-Type: application/json"
```

### 3. API 文档端点

#### GET /docs

FastAPI 自动生成的交互式 API 文档，可通过浏览器访问。

## 错误处理

- `422 Unprocessable Entity`: 无效请求输入（JSON验证失败）
- `500 Internal Server Error`: 服务器内部错误（如邮件搜索失败）

## CORS 配置

该 API 的 CORS 策略允许以下来源：
- `http://localhost`
- `http://localhost:3000`