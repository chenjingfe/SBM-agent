# SBM Agent

豆粕 ETF 多 Agent 交易系统后端基础框架。版本：0.2.0；更新日期：2026-09-26。

依据根目录技术方案 v0.3 构建。当前仅交付 API 骨架与人工输入的溢价率计算，不是完整交易系统。

## 当前能力

- FastAPI 应用工厂、生命周期、SBM_ 配置注入，保留 `python -m app`。
- 五模块状态入口，区分 C 端 `/client`、B 端 `/admin` 和公共 `/auth`。
- CORS、请求链路 ID、基础日志、统一错误结构、Pydantic 校验。
- Decimal 溢价率纯计算；严格小于 2% 或严格大于 6% 命中，等于边界不命中。
- 模块状态一律标记 `planned/scaffold`；无实际行情、Agent、登录、数据库或下单。
- B 端鉴权/RBAC 尚未实现，管理入口默认拒绝访问，返回 503。

## 代码结构

```text
src/app/
├── api/dependencies.py  配置注入与管理入口门禁
├── api/router.py        公共、C/B 端和兼容路由
├── api/routes/          五模块、健康检查、溢价率预览
├── core/                配置、错误处理、请求中间件
├── schemas/             Pydantic 请求响应模型
├── services/            与 HTTP 解耦的业务计算
├── main.py              应用工厂与生命周期
└── __main__.py          python -m app 入口
```

## 安装和启动

使用 Python 3.12，从项目根目录执行；仅在 `.venv` 不存在时运行 `py -3.12 -m venv .venv`。

```powershell
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
$env:PYTHONPATH = "src"
& ./.venv/Scripts/python.exe -m app
```

默认地址 `http://127.0.0.1:8000`，用 `Ctrl+C` 停止。验证与安全能力完善前不要暴露公网。

**本地验证状态（2026-09-26）：** 用户已在本机终端成功安装依赖。项目解释器的 pip check、语法和应用导入检查通过；63 项进程内接口/配置检查、21 项独立服务真实 HTTP 检查通过。验证用临时进程已停止，目前未保留开发服务。这里只验证基础框架，不代表真实行情、Agent 或交易业务已完成，详见 `后端开发记录.md`。

## 接口

- `GET /health`：API 存活响应，`scope=api_only`，不检查外部依赖。
- `GET /docs`、`GET /redoc`、`GET /openapi.json`：文档，可一起关闭。
- `GET /api/v1/auth/status`：鉴权模块规划，不是登录接口。
- `GET /api/v1/client/market/status`：行情模块规划。
- `GET /api/v1/client/trading/status`：交易规划、配置阈值、四类 Agent 规划。
- `GET /api/v1/client/review/status`：复盘模块规划。
- `GET /api/v1/client/knowledge/status`：知识库模块规划。
- `POST /api/v1/client/trading/premium/evaluate`：人工输入的纯计算预览。
- `GET /api/v1/admin/status`：未配置鉴权，始终返回 503。

旧版 `/api/v1/{market,trading,review,knowledge}/status` 保留为弃用兼容入口。内部接口、WebSocket 未注册。C 端仅有无账户信息的状态与纯计算；后续私有数据和订单接口必须先接入鉴权，管理入口 503 不代表完整 RBAC。

## 溢价率预览

以下是虚构的计算示例，不代表基金行情：

```powershell
$body = @{ instrument = "EXAMPLE"; market_price = "1.02"; reference_nav = "1.00" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/client/trading/premium/evaluate -ContentType application/json -Body $body
```

- 公式：`(market_price - reference_nav) / reference_nav`；比率 `0.02` 表示 2%。
- 价格、净值须正且有限；最多 18 位数字、8 位小数，拒绝额外输入字段。
- 净值口径、来源和时效当前不校验；不可据此直接交易。
- 2%/6% 边界返回 `NORMAL`，折价亦命中低于 2% 的条件。
- Decimal 通过 JSON 十进制字符串返回，不是百分数。
- 始终返回 `analysis_started=false`、`scope=calculation_only`、`data_quality=unverified`。
- 命中条件不等于运行 Agent 或下单；生产触发须增加数据质量、防抖、投票、确定性风控和执行门禁。

## 配置

环境变量优先于项目根目录 `.env`，最后使用代码默认值；`.env` 位置由源码确定，不依赖启动目录。

- `SBM_ENVIRONMENT`：development/test/production，默认 development。
- `SBM_HOST`、`SBM_PORT`：默认 127.0.0.1:8000，端口范围 1–65535。
- `SBM_API_V1_PREFIX`：默认 /api/v1，不得以斜杠结尾。
- `SBM_RELOAD`：默认 false；示例配置为本地开发启用 true。
- `SBM_DOCS_ENABLED`：默认 true；false 关闭全部文档入口。
- `SBM_LOG_LEVEL`：DEBUG/INFO/WARNING/ERROR，默认 INFO。
- `SBM_CORS_ORIGINS`：JSON 数组，默认本机 5173/5174 来源，禁止通配符。
- `SBM_PREMIUM_LOWER_THRESHOLD`、`SBM_PREMIUM_UPPER_THRESHOLD`：0.02/0.06；下限须小于上限，策略修改须经批准。

不要把凭证写入源码、提示词或普通日志。当前仅标记模拟盘模式，无执行适配器。

## 错误与日志

应用请求带服务端生成的 `X-Request-ID`，错误结构示例：

```json
{"error":{"code":"VALIDATION_ERROR","message":"Invalid request data.","trace_id":"...","details":[]}}
```

非法参数 422、未知路径 404、管理能力未配置 503；未处理异常在响应开始前返回脱敏 500。校验错误不返回原始输入和 Pydantic 上下文；流式响应已开始后不能重写 JSON。CORS 预检由外层中间件处理，不经过应用链路中间件。

`python -m app` 关闭 Uvicorn 原始访问日志；应用日志记录链路 ID、方法、路由模板、状态码、耗时、异常类型，不记录请求体、查询参数、凭据或异常正文。其他启动方式须保持日志约束。当前日志不是持久化审计，未接入 Loki/OTel。

## 验证

```powershell
& ./.venv/Scripts/python.exe -m compileall -q src
$env:PYTHONPATH = "src"
& ./.venv/Scripts/python.exe -c "from app.main import app; print(app.title)"
```

本次已分别完成依赖导入、进程内接口检查和独立服务真实 HTTP 检查，覆盖 `/health`、五模块、四个兼容入口、计算边界、非法输入 422、管理入口 503、未知路径 404、链路 ID 和 CORS；进程内检查另覆盖 500 脱敏、自定义配置及文档开关。后续修改仍须按受影响范围重验，语法成功不能替代导入与 HTTP 验证。

## 后续组件

保留既有 langchain==1.4.2 依赖声明，本阶段不调用模型。AKShare、LangGraph、APScheduler、Celery + Redis、PostgreSQL/TimescaleDB/pgvector、bge-m3、分析回测、完整鉴权、容器和观测按阶段接入；技术选型不代表实现完成。
