# AI日本考学推荐系统

基于大语言模型的日本大学院择校推荐与留学顾问平台。支持多AI模型动态切换、RAG知识库检索、流式对话与择校推荐。

## 技术架构

```
┌─────────────┐      ┌─────────────┐      ┌─────────────────┐
│  Next.js    │──────▶│   NestJS    │──────▶│  FastAPI (AI)   │
│  Frontend   │      │   Backend   │      │  Provider Layer │
└─────────────┘      └──────┬──────┘      └─────────────────┘
                            │
                     ┌──────┴──────┐
                     │ PostgreSQL  │
                     │  + pgvector │
                     └─────────────┘
```

- **Frontend**: Next.js 15 + React 19 + Tailwind CSS + Zustand
- **Backend**: NestJS + Prisma + PostgreSQL + JWT Auth + Rate Limiting
- **AI Service**: FastAPI + 统一Provider接口 + LangChain RAG + pgvector

## 支持的AI模型

| 模型 | Provider | 流式 | Embedding |
|------|----------|------|-----------|
| GPT-4o / GPT-4o-mini | OpenAI | 支持 | 支持 |
| Claude Opus 4 / Sonnet 4 | Anthropic | 支持 | - |
| DeepSeek Chat / Reasoner | DeepSeek | 支持 | - |
| Gemini 1.5 Pro / Flash | Google | 支持 | 支持 |
| 火山引擎 | Volcengine | 支持 | - |

支持 **Fallback 自动降级**：当主模型不可用时，自动按预设链切换备用模型。

## 核心功能

1. **AI择校推荐**
   - 输入GPA、语言成绩、本科背景、预算
   - AI输出：冲刺校 / 稳妥校 / 保底校 + 匹配度 + 推荐理由

2. **AI聊天顾问**
   - 多轮对话 + 上下文记忆（最近20条）
   - 流式SSE输出 + 模型切换
   - 会话历史管理

3. **RAG知识库**
   - 来源：日本大学募集要项、教授主页、留学FAQ
   - 技术：LangChain + text-embedding + pgvector HNSW检索
   - 回答带引用来源

4. **AI Provider Layer**
   - 统一OpenAI Compatible接口封装
   - 动态模型切换 + Fallback链
   - Token统计 + 成本估算
   - Redis双层限流（用户级 + 全局级）

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的AI API Keys
```

### 2. Docker Compose 启动

```bash
docker-compose up --build
```

服务将启动在：
- Frontend: http://localhost:3000
- Backend API: http://localhost:3001
- Backend Swagger: http://localhost:3001/docs
- AI Service: http://localhost:8000

### 3. 初始化数据库

```bash
# 进入backend容器
docker-compose exec backend npx prisma migrate dev --name init
```

## 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL连接字符串 | - |
| `REDIS_URL` | Redis连接字符串 | redis://redis:6379 |
| `JWT_SECRET` | JWT签名密钥 | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `ANTHROPIC_API_KEY` | Claude API Key | - |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `GEMINI_API_KEY` | Gemini API Key | - |
| `VOLCENGINE_API_KEY` | 火山引擎 API Key | - |
| `VOLCENGINE_ENDPOINT_ID` | 火山引擎 Endpoint ID | - |
| `DEFAULT_MODEL` | 默认模型 | gpt-4o |

## API 端点

### AI Service (FastAPI)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/models` | 列出可用模型 |
| POST | `/chat` | 普通聊天 |
| POST | `/chat/stream` | 流式聊天 (SSE) |
| POST | `/embeddings` | 文本Embedding |
| POST | `/recommend` | 择校推荐 |
| POST | `/rag/query` | RAG问答 |
| POST | `/rag/query/stream` | RAG流式问答 |
| POST | `/rag/documents` | 添加知识库文档 |

### Backend (NestJS)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| GET | `/users/me` | 当前用户 |
| GET | `/users/profiles` | 学生档案列表 |
| POST | `/recommendations` | 提交推荐请求 |
| GET | `/recommendations` | 推荐历史 |
| GET/POST | `/chat/sessions` | 聊天会话 |
| POST | `/chat/sessions/:id/messages` | 发送消息 |
| POST | `/documents/search` | 知识库搜索 |
| GET | `/universities` | 大学列表 |

## 项目结构

```
japan-uni-assist/
├── docker-compose.yml
├── .env.example
├── ai-service/           # FastAPI AI服务
│   ├── src/
│   │   ├── main.py
│   │   ├── providers/    # 5个Provider实现
│   │   ├── rag/          # Embedding + Retriever + Chain
│   │   ├── recommend/    # 择校推荐逻辑
│   │   └── utils/        # 配置、日志、限流
│   └── scripts/
├── backend/              # NestJS后端
│   ├── prisma/
│   │   └── schema.prisma
│   └── src/
│       ├── auth/         # JWT认证
│       ├── users/
│       ├── recommendations/
│       ├── chat/
│       ├── documents/
│       └── universities/
└── frontend/             # Next.js前端
    └── src/
        ├── app/          # 页面路由
        ├── components/   # UI组件
        ├── lib/          # API客户端
        └── types/        # TypeScript类型
```

## 安全设计

- API Key仅通过环境变量注入，绝不暴露给前端
- 前端所有AI调用经 Backend → AI-Service 代理
- JWT HttpOnly风格认证（localStorage存储token）
- 双层限流：NestJS Throttler（HTTP层）+ Redis Token Bucket（AI调用层）
- 结构化JSON日志，敏感信息脱敏

## License

MIT