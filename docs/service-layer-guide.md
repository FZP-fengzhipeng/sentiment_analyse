# Service 层学习方案

这份文档用于你面试前快速吃透本项目的 service 层。

目标不是逐行背代码，而是搞懂：

```text
router 层接收请求
-> service 层组织业务
-> engines 层执行核心能力
-> service 层把结果返回给 router
```

## 1. Service 层是干什么的

在这个项目里，service 层主要负责业务编排。

router 层只做：

```text
接收参数
调用 service
返回 response
处理异常
```

service 层负责：

```text
读配置
启动研究任务
控制主持人 Agent
管理报告生成任务
推送实时进度
协调生命周期
```

可以记一句：

```text
router 是接口入口，service 是业务入口，engines 是核心执行引擎。
```

## 2. 先看 dependencies.py

文件：

```text
app/dependencies.py
```

重点看这些对象：

```python
_config_service = ConfigService()
_research_service = ResearchService()
_report_service = ReportService(task_store=ReportTaskStore())
_host_service = HostService()
_broadcaster_service = BroadcasterService()
```

这里做的是模块级单例。

也就是：

```text
服务对象在模块加载时创建一次
后续 router 通过 Depends 拿到同一个对象
```

重点看这些依赖别名：

```python
ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]
ResearchServiceDep = Annotated[ResearchService, Depends(get_research_service)]
HostServiceDep = Annotated[HostService, Depends(get_host_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
```

面试说法：

```text
项目通过 dependencies.py 统一管理 service 实例，并用 FastAPI 的 Depends 做依赖注入。这样 router 不需要自己创建 service，只需要声明参数即可。
```

## 3. ConfigService

文件：

```text
app/services/system/config_service.py
```

主要方法：

```python
read_config_info()
update_config_info(update_info)
```

### read_config_info

作用：

```text
读取当前系统配置，返回给前端配置页面展示。
```

它从 `get_settings()` 获取当前配置，只返回 `CONFIG_KEYS` 里声明的配置项。

### update_config_info

作用：

```text
把前端传来的配置写入 .env，并重新加载配置。
```

核心逻辑：

```python
set_key(env_file_path, key, str(value))
os.environ[key] = value
return reload_settings()
```

也就是：

```text
1. 写入 .env 文件
2. 同步当前进程环境变量
3. 触发配置热加载
```

面试说法：

```text
ConfigService 负责配置读写。前端提交配置后，后端写入 .env，同时更新 os.environ，并调用 reload_settings 让新配置生效。
```

## 4. ResearchService

文件：

```text
app/services/research/research_service.py
```

主要方法：

```python
start_research(query)
get_research_result()
```

你要重点搞懂：

```text
它是研究任务的启动入口。
```

业务链路：

```text
前端输入研究主题
-> POST /api/research/start
-> router 调 ResearchService.start_research(query)
-> service 启动研究编排
-> Insight Agent 和 Media Agent 开始生成报告
-> 保存各自结果
```

你看代码时重点追：

```text
start_research 调用了哪个 orchestration 方法
研究结果保存在哪里
get_research_result 返回什么结构
```

面试说法：

```text
ResearchService 是研究流程入口，它不直接写 Agent 细节，而是调用 orchestration 层启动公域和私域 Agent，然后提供结果查询接口给前端。
```

## 5. HostService

文件：

```text
app/services/host/host_service.py
app/services/host/discuss_buffer.py
```

主要方法：

```python
start_host()
stop_host()
get_discussion_records()
get_research_dimensions()
```

### start_host

作用：

```text
启动主持人监听器 SectionReadyListener。
```

核心逻辑：

```python
if self._listener is not None:
    return True

self._listener = SectionReadyListener()
self._listener.start()
```

意思是：

```text
如果已经启动，就不重复启动。
如果没启动，就创建监听器并启动。
```

### stop_host

作用：

```text
停止主持人监听器。
```

### discussion_buffer

作用：

```text
缓存主持人讨论记录，供前端查询展示。
```

### HostService 的核心理解

主持人 Agent 不是前端一请求就直接生成报告。

它更像一个监听者：

```text
Insight Agent 完成一个章节
-> 发布 section_ready 事件

Media Agent 完成一个章节
-> 发布 section_ready 事件

Host 的 SectionReadyListener 收到事件
-> 收集章节内容
-> 触发主持人研判
-> 缓存讨论记录
```

面试说法：

```text
HostService 负责控制主持人研判流程。它通过 SectionReadyListener 监听 section_ready 事件，把 Insight 和 Media 两个 Agent 的章节结果收集起来，再组织主持人维度研判。
```

## 6. BroadcasterService

文件：

```text
app/services/realtime/broadcaster_service.py
```

它服务于 SSE 接口：

```text
GET /api/events/stream
```

主要作用：

```text
把后端研究进度实时推送给前端。
```

典型流程：

```text
前端 new EventSource('/api/events/stream')
-> 后端建立 SSE 长连接
-> Agent 执行过程中上报 progress
-> BroadcasterService 推送事件
-> 前端实时更新进度条/状态卡片
```

你要重点看：

```text
stream_research_progress(request)
broadcast 相关方法
队列或订阅者如何维护
request.is_disconnected() 如何处理断开连接
```

面试说法：

```text
项目使用 SSE 推送长任务进度，因为研究任务耗时较长，如果只用普通 HTTP 请求，前端无法实时知道 Agent 执行状态。SSE 比轮询更实时，也比 WebSocket 更轻量。
```

## 7. ReportService

文件：

```text
app/services/report/report_service.py
app/services/report/input_loader.py
app/services/report/task_store.py
```

主要方法：

```python
get_report_status()
start_generate_report_task(query)
get_generate_report_task(task_id)
get_download_file(task_id, file_type)
```

### get_report_status

作用：

```text
检查最终报告生成所需的输入文件是否准备好。
```

它会检查：

```text
Insight 报告
Media 报告
Host 报告
```

然后返回：

```python
{
    "prepared": True 或 False,
    "found_files": [...]
}
```

### start_generate_report_task

作用：

```text
创建报告生成任务，并在后台异步执行。
```

核心逻辑：

```python
task = self._task_store.create_generate_task()
asyncio.create_task(self._run_report_generation(task, query))
return task
```

为什么这么做：

```text
报告生成可能很慢，不能让接口一直阻塞等待。
所以先创建 task_id 返回给前端，后台慢慢生成。
```

### _run_report_generation

完整链路：

```text
检查输入文件是否准备好
-> 加载 Insight/Media/Host 的报告内容
-> 调用 ReportEngine 生成最终报告
-> 保存 HTML 和 Markdown
-> 更新任务状态为完成
```

### task_store

作用：

```text
保存报告生成任务状态。
```

前端拿到 `task_id` 后，可以继续查：

```text
GET /api/report/result/{task_id}
GET /api/report/download/{task_id}/{file_type}
```

面试说法：

```text
ReportService 负责最终综合报告生成。它先检查三个输入报告是否准备好，然后创建异步任务，后台调用 ReportEngine 生成 HTML 和 Markdown，并通过 task_store 保存任务状态。
```

## 8. LifecycleService

文件：

```text
app/services/lifecycle/lifecycle_service.py
```

它和 FastAPI 的 `lifespan` 配合。

在 `app/app.py` 里：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    lifecycle_service = get_lifecycle_service()
    try:
        lifecycle_service.register()
        yield
    finally:
        lifecycle_service.shutdown()
```

作用：

```text
应用启动时注册事件监听/广播协调逻辑。
应用关闭时释放资源。
```

面试说法：

```text
LifecycleService 用来统一管理应用启动和关闭时需要注册或释放的服务，避免把生命周期逻辑散落在 router 或 service 里。
```

## 9. 推荐阅读顺序

按这个顺序看：

```text
1. app/dependencies.py
2. app/services/system/config_service.py
3. app/services/research/research_service.py
4. app/services/host/host_service.py
5. app/services/host/discuss_buffer.py
6. app/services/realtime/broadcaster_service.py
7. app/services/report/report_service.py
8. app/services/report/input_loader.py
9. app/services/report/task_store.py
10. app/services/lifecycle/lifecycle_service.py
```

每个文件只抓三个问题：

```text
1. 它被哪个 router 调用？
2. 它调用了哪个 engine 或工具？
3. 它返回什么给前端？
```

## 10. Service 层总流程图

```text
前端页面
  |
  v
router 层
  |
  v
service 层
  |
  +--> ConfigService
  |      读写 .env 配置
  |
  +--> ResearchService
  |      启动 Insight / Media 研究任务
  |
  +--> HostService
  |      启动主持人监听 section_ready 事件
  |
  +--> BroadcasterService
  |      通过 SSE 推送实时进度
  |
  +--> ReportService
         聚合报告输入，生成最终报告
```

## 11. 面试高频问题

### 为什么要有 service 层？

```text
为了把接口处理和业务逻辑分开。router 只负责接请求和返回响应，service 负责业务编排。这样代码更清晰，也方便测试和维护。
```

### 为什么 service 通过 Depends 注入？

```text
可以统一管理 service 实例，避免每个接口里手动创建对象。项目里用 dependencies.py 创建模块级单例，再通过 Depends 注入到路由函数。
```

### ResearchService 和 Agent 是什么关系？

```text
ResearchService 是业务入口，Agent 是具体执行者。ResearchService 接收 query 后，调用 orchestration 层启动 Insight Agent 和 Media Agent。
```

### HostService 为什么需要 listener？

```text
因为主持人需要等待其他 Agent 完成章节。Insight 和 Media 每完成一个章节会发布 section_ready 事件，HostService 通过 SectionReadyListener 监听这些事件并做后续研判。
```

### ReportService 为什么用 task_store？

```text
最终报告生成是耗时任务，不能让接口一直阻塞。task_store 用来保存任务状态，前端拿到 task_id 后可以查询结果或下载文件。
```

### 为什么用 SSE？

```text
研究流程是长任务，前端需要实时看到进度。SSE 可以让后端持续推送事件，比轮询更实时，比 WebSocket 更轻量。
```

## 12. 你要能讲出来的一句话

```text
这个项目的 service 层负责把前端请求转成具体业务流程。ConfigService 管配置，ResearchService 启动研究，HostService 管主持人监听，BroadcasterService 推送实时进度，ReportService 生成最终综合报告。router 层只负责接入，真正的业务编排都在 service 层完成。
```
