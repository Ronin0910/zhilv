<p align="center">
  <h1 align="center">🌟 智旅星图 · AI智能旅行规划平台</h1>
  <p align="center">
    基于多智能体协作与RAG技术的AI旅行规划助手
    <br />
    <a href="#快速开始"><strong>快速开始 »</strong></a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#api接口文档"><strong>API文档 »</strong></a>
    &nbsp;&nbsp;·&nbsp;&nbsp;
    <a href="#项目架构"><strong>项目架构 »</strong></a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js&logoColor=white" alt="Vue">
  <img src="https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/LangChain-latest-000000?logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Pinecone-Vector_DB-000000?logo=pinecone&logoColor=white" alt="Pinecone">
  <img src="https://img.shields.io/badge/高德地图-MCP_Server-0052CC?logo=amap&logoColor=white" alt="Amap">
  <img src="https://img.shields.io/badge/通义千问-DashScope-6D5FEA?logo=alibabacloud&logoColor=white" alt="DashScope">
  <img src="https://img.shields.io/badge/Ant_Design_Vue-4.x-0170FE?logo=antdesign&logoColor=white" alt="Ant Design Vue">
</p>

---

## 📖 项目简介

**智旅星图** 是一个基于 AI 的智能旅行规划平台，核心功能包括：

- 🤖 **多智能体行程规划** — 4个专职AI Agent并行协作，自动生成结构化行程方案
- 📚 **RAG知识库问答** — 基于检索增强生成的旅游知识问答，支持SSE流式输出
- 🗺️ **高德地图深度集成** — MCP协议对接 + REST API双通道，提供POI搜索、路线规划、天气查询
- 📊 **可视化行程展示** — 交互式地图标记、预算分析、天气预报、导出分享

> 项目同时接入了 **MCP (Model Context Protocol)** 协议，通过高德 MCP Server 为 AI Agent 提供地图工具能力。

---

## 🏗️ 项目架构

```
trip-planner/
├── backend/                    # 后端服务 (Python + FastAPI)
│   ├── app/
│   │   ├── api/                # API路由层
│   │   │   ├── main.py         # FastAPI应用入口、CORS、生命周期
│   │   │   └── routes/
│   │   │       ├── trip.py     # 行程规划接口
│   │   │       ├── map.py      # 地图服务接口 (MCP)
│   │   │       ├── poi.py      # POI详情/搜索/图片接口
│   │   │       └── qa.py       # RAG问答接口 (SSE流式)
│   │   ├── agents/             # AI Agent层
│   │   │   ├── trip_planner_agent.py   # 多智能体行程规划器
│   │   │   └── rag_agent.py            # RAG问答Agent
│   │   ├── services/           # 服务层
│   │   │   ├── amap_service.py         # 高德MCP客户端 + REST API
│   │   │   ├── llm_service.py          # LLM模型封装 (DashScope)
│   │   │   ├── embedding_service.py    # Embedding模型封装
│   │   │   ├── vector_store.py         # Pinecone向量数据库
│   │   │   ├── document_loader.py      # 文档加载与分块
│   │   │   ├── memory_service.py       # Redis会话记忆
│   │   │   ├── memory_service_mongo.py # MongoDB会话记忆 (备选)
│   │   │   └── unsplash_service.py     # Unsplash图片服务
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic数据模型 (20+)
│   │   ├── rag/
│   │   │   └── prompts.py      # RAG提示词模板
│   │   └── config.py           # 配置管理 (pydantic-settings)
│   ├── knowledge/              # 知识库文档
│   ├── scripts/
│   │   └── build_index.py      # 向量索引构建脚本
│   ├── requirements.txt        # Python依赖
│   └── run.py                  # 启动入口
│
├── frontend/                   # 前端应用 (Vue 3 + TypeScript)
│   └── src/
│       ├── views/
│       │   ├── Home.vue        # 首页 - 行程规划表单
│       │   ├── Result.vue      # 结果页 - 行程展示 + 地图
│       │   └── QA.vue          # 问答页 - AI对话界面
│       ├── services/
│       │   └── api.ts          # API客户端 + SSE流式解析
│       ├── types/
│       │   └── index.ts        # TypeScript类型定义
│       ├── App.vue             # 应用外壳
│       └── main.ts             # 应用入口
│
└── README.md                   # 项目说明文档
```

### 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
│  Home.vue ──────► Result.vue        QA.vue                      │
│  (表单输入)       (行程展示+地图)    (AI对话+SSE)                │
└─────────────┬───────────────────────────────┬───────────────────┘
              │ Axios / Fetch + SSE           │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ Trip Planner │   │  Map Service │   │   RAG Q&A    │        │
│  │  (4 Agents)  │   │   (MCP+REST) │   │  (Agent+RAG) │        │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│         │                  │                   │                │
│         ▼                  ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              LangChain Agent Framework               │       │
│  └───┬─────────────┬──────────────┬────────────┬───────┘       │
│      │             │              │            │                │
│      ▼             ▼              ▼            ▼                │
│  高德MCP      DashScope       Pinecone      Redis              │
│  Server       (LLM+Emb)      (VectorDB)    (Memory)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心功能

### 1. 🤖 多智能体行程规划

采用 **4个专职AI Agent** 并行协作的方式生成旅行方案：

| Agent | 职责 | 工具 |
|-------|------|------|
| 🏛️ **景点Agent** | 根据偏好搜索景点 | 高德MCP `maps_text_search` |
| 🌤️ **天气Agent** | 查询目的地天气 | 高德MCP `maps_weather` |
| 🏨 **酒店Agent** | 搜索推荐酒店 | 高德MCP `maps_text_search` |
| 📋 **规划Agent** | 综合信息生成行程 | 纯LLM推理 |

**工作流程：**
1. 前3个Agent通过 `asyncio.gather` **并行执行**
2. 规划Agent汇总所有结果，输出结构化JSON行程
3. 自动为每个景点获取实景图片
4. 包含容错机制，任一Agent失败仍可生成方案

### 2. 📚 RAG智能问答

完整的 **检索增强生成 (RAG)** 流程：

```
用户提问 ──► 语义检索(Pinecone) ──► 有结果? ──Yes──► 注入上下文 ──► LLM生成回答
                                        │
                                        No
                                        │
                                        ▼
                                   Tavily网络搜索 ──► 注入搜索结果 ──► LLM生成回答
```

- **知识库构建**：支持PDF/TXT/MD文档，自动分块、向量化、存入Pinecone
- **混合检索**：优先知识库检索，无结果时自动回退到Tavily网络搜索
- **会话记忆**：Redis存储对话历史，滑动窗口保留最近10轮
- **流式输出**：SSE (Server-Sent Events) 实时推送，逐token生成

### 3. 🗺️ 高德地图集成

采用 **MCP + REST API 双通道** 架构：

| 通道 | 用途 | 技术 |
|------|------|------|
| **MCP Server** | AI Agent工具调用 | `langchain-mcp-adapters` + stdio |
| **REST API** | 程序化数据获取 | `requests` HTTP客户端 |

提供能力：
- POI搜索与详情查询
- 天气预报
- 路线规划（步行/驾车/公交）
- 静态地图生成（导出用）
- 景点实景图片

### 4. 📊 行程可视化

- **交互式地图**：高德JS API 2.0，景点编号标记、每日路线连线、信息窗口
- **行程卡片**：可折叠的每日行程，含景点信息、酒店推荐、用餐安排
- **预算分析**：景点门票、酒店、餐饮、交通分项统计
- **天气预报**：目的地天气展示
- **导出功能**：支持导出为PNG图片或PDF文档

---

## 🛠️ 技术栈

### 后端

| 类别 | 技术 |
|------|------|
| **Web框架** | FastAPI + Uvicorn |
| **AI框架** | LangChain (Agents, Tools, Chat Models) |
| **LLM模型** | 通义千问 `qwen-plus` (DashScope) |
| **Embedding** | `text-embedding-v2` (DashScope) |
| **向量数据库** | Pinecone |
| **会话存储** | Redis (主) / MongoDB (备选) |
| **地图服务** | 高德MCP Server + REST API |
| **网络搜索** | Tavily Search |
| **数据校验** | Pydantic v2 |
| **配置管理** | pydantic-settings + python-dotenv |

### 前端

| 类别 | 技术 |
|------|------|
| **框架** | Vue 3.5 (Composition API) |
| **构建工具** | Vite 6 |
| **语言** | TypeScript |
| **UI组件库** | Ant Design Vue 4.2 |
| **路由** | Vue Router 4.5 |
| **HTTP客户端** | Axios |
| **地图** | 高德JS API 2.0 |
| **导出** | html2canvas + jsPDF |
| **Markdown** | marked |

---

## 🚀 快速开始

### 环境要求

- **Python** >= 3.10
- **Node.js** >= 18
- **Redis** 服务运行中

### 1. 克隆项目

```bash
git clone https://github.com/your-username/trip-planner.git
cd trip-planner
```

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**配置环境变量**：复制并编辑 `.env` 文件

```bash
cp .env.example .env   # 如果有的话，否则直接编辑 .env
```

需要配置的API密钥：

```env
# LLM模型 (必需)
LLM_API_KEY=your_dashscope_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_ID=qwen-plus
LLM_EMBEDDING_MODEL=text-embedding-v2

# 高德地图 (必需)
AMAP_API_KEY=your_amap_api_key

# Pinecone向量数据库 (RAG功能必需)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=travel-knowledge
PINECONE_NAMESPACE=travel

# Redis (必需)
REDIS_URL=redis://localhost:6379/0

# Tavily网络搜索 (可选)
TAVILY_API_KEY=your_tavily_api_key

# Unsplash图片 (可选)
UNSPLASH_ACCESS_KEY=your_unsplash_key
```

**启动后端服务**：

```bash
python run.py
# 服务将在 http://localhost:8000 启动
```

**（可选）构建向量知识库**：

```bash
# 将文档放入 knowledge/ 目录，然后执行
python scripts/build_index.py
```

### 3. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 前端将在 http://localhost:5173 启动，自动代理API请求到后端
```

### 4. 访问应用

打开浏览器访问 **http://localhost:5173**，即可开始使用：

- **首页** `/` — 输入目的地、日期、偏好，AI生成行程方案
- **结果页** `/result` — 查看完整行程、地图、预算，支持导出
- **问答页** `/qa` — 与AI对话，咨询旅游相关问题

---

## 📡 API接口文档

### 行程规划

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/trip/plan` | 生成旅行方案 |
| `GET` | `/api/trip/health` | 服务健康检查 |

**请求示例**：
```json
{
  "city": "北京",
  "start_date": "2025-04-01",
  "end_date": "2025-04-03",
  "days": 3,
  "transport": "公共交通",
  "accommodation": "舒适型",
  "preferences": ["历史文化", "美食"],
  "free_text": "希望行程不要太赶"
}
```

### POI服务

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/poi/detail/{poi_id}` | 获取POI详情 |
| `GET` | `/api/poi/search?keywords=&city=` | 搜索POI |
| `GET` | `/api/poi/photo?name=&city=` | 获取景点图片 |
| `GET` | `/api/poi/proxy-image?url=` | 图片代理(解决CORS) |

### 地图服务

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/map/poi?keywords=&city=` | MCP POI搜索 |
| `GET` | `/api/map/weather?city=` | 天气查询 |
| `POST` | `/api/map/route` | 路线规划 |
| `GET` | `/api/map/static-map` | 静态地图生成 |
| `GET` | `/api/map/health` | 地图服务健康检查 |

### RAG问答

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/qa/chat` | SSE流式问答 |
| `DELETE` | `/api/qa/session/{id}` | 清除会话历史 |
| `GET` | `/api/qa/health` | 问答服务健康检查 |

**SSE事件类型**：
- `token` — 流式输出的文本片段
- `done` — 生成完成
- `error` — 发生错误

---

## 🧩 项目亮点

### 技术深度

1. **多智能体并行协作** — 3个专职Agent通过 `asyncio.gather` 并行执行，第4个Agent综合生成结构化方案，相比串行调用效率提升约3倍
2. **MCP协议实践** — 基于 `langchain-mcp-adapters` 对接高德MCP Server，AI Agent通过stdio通信调用地图工具
3. **RAG全链路实现** — 文档加载 → 语义分块 → 向量化 → Pinecone存储 → 相似度检索 → 提示词注入 → 流式生成
4. **双通道架构** — MCP通道供AI Agent工具调用，REST通道供程序化数据获取，互不干扰

### 工程实践

5. **健壮的JSON解析** — 多层提取策略（Markdown代码块匹配 → 花括号匹配 → Pydantic校验）+ 降级方案
6. **SSE流式输出** — 基于 `StreamingResponse` 实现服务端推送，前端通过 `ReadableStream` 解析
7. **会话记忆管理** — Redis List实现对话历史，滑动窗口 + TTL自动过期
8. **CORS图片代理** — 导出功能通过服务端代理解决跨域图片访问问题

### 用户体验

9. **交互式地图展示** — 高德JS API 2.0实现景点标记、路线绘制、信息窗口
10. **多格式导出** — 支持PNG图片和PDF文档导出，地图自动替换为静态图片
11. **渐进式加载** — 行程生成时展示动画进度条和状态提示，流式问答逐字输出

---

## 📁 关键文件说明

| 文件 | 说明 |
|------|------|
| [backend/app/agents/trip_planner_agent.py](backend/app/agents/trip_planner_agent.py) | 多智能体行程规划核心，4个Agent的定义与编排 |
| [backend/app/agents/rag_agent.py](backend/app/agents/rag_agent.py) | RAG问答Agent，集成知识库检索和网络搜索 |
| [backend/app/services/amap_service.py](backend/app/services/amap_service.py) | 高德MCP客户端，管理MCP Server生命周期 |
| [backend/app/services/vector_store.py](backend/app/services/vector_store.py) | Pinecone向量数据库操作 |
| [backend/app/services/memory_service.py](backend/app/services/memory_service.py) | Redis会话记忆管理 |
| [backend/app/models/schemas.py](backend/app/models/schemas.py) | 全部Pydantic数据模型定义 |
| [frontend/src/views/Result.vue](frontend/src/views/Result.vue) | 行程结果展示，含交互式地图和导出功能 |
| [frontend/src/views/QA.vue](frontend/src/views/QA.vue) | AI问答界面，SSE流式对话 |
| [frontend/src/services/api.ts](frontend/src/services/api.ts) | API客户端与SSE流式解析 |



## 📄 开源协议

本项目仅供学习交流使用。

---

<p align="center">
  如果这个项目对你有帮助，欢迎 ⭐ Star 支持一下！
</p>
