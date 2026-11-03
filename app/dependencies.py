"""应用依赖注入中心：统一管理全局服务单例与 FastAPI 依赖项注入"""

from typing import Annotated

from fastapi import Depends

from app.services.host.host_service import HostService
from app.services.lifecycle.lifecycle_service import AppServiceEventCoordinator
from app.services.realtime.broadcaster_service import BroadcasterService
from app.services.report.report_service import ReportService
from app.services.report.task_store import ReportTaskStore
from app.services.research.research_service import ResearchService
from app.services.system.config_service import ConfigService

_config_service = ConfigService()


def get_config_service() -> ConfigService:
    """提供全局应用配置服务单例。"""
    return _config_service


_research_service = ResearchService()


def get_research_service() -> ResearchService:
    """提供全局研究工作流服务单例。"""
    return _research_service


_report_service = ReportService(task_store=ReportTaskStore())


def get_report_service() -> ReportService:
    """提供全局报告生成服务单例。"""
    return _report_service


_host_service = HostService()


def get_host_service() -> HostService:
    """提供全局主持人研判服务单例。"""
    return _host_service


_broadcaster_service = BroadcasterService()


def get_sse_broadcaster() -> BroadcasterService:
    """提供全局SSE事件广播器单例。"""
    return _broadcaster_service


def get_lifecycle_service() -> AppServiceEventCoordinator:
    """构建协调监听与广播的生命周期管理器。"""
    return AppServiceEventCoordinator(_host_service, _broadcaster_service)


ConfigServiceDep = Annotated[ConfigService, Depends(get_config_service)]
ResearchServiceDep = Annotated[ResearchService, Depends(get_research_service)]
HostServiceDep = Annotated[HostService, Depends(get_host_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
LifecycleServiceDep = Annotated[AppServiceEventCoordinator, Depends(get_lifecycle_service)]

#这段代码是在给 FastAPI 的依赖注入做类型别名封装。ResearchServiceDep 这个类型代表：
#它的真实类型是 ResearchService，
#但它的值由 get_research_service() 这个依赖函数提供。

#所以你后面路由里可以写：
#async def start_research_endpoint(
#    payload: ResearchRequest,
#    service: ResearchServiceDep,
#):
#    ...

#它等价于写：
##async def start_research_endpoint(
#    payload: ResearchRequest,
#    service: Annotated[ResearchService, Depends(get_research_service)],
#):
#    ...
