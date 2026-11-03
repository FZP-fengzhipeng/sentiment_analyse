from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from engines.insight_agent.tools.platform_mappings import (
    PLATFORM_MAPPING,
    ContentTableMapping,
    CommentTableMapping,
)
from engines.insight_agent.tools.vector_search.search_results import VectorDocument
from engines.insight_agent.tools.vector_search.source.models import (
    DouyinAweme,
    DouyinAwemeComment,
    VectorSourceBase,
    WeiboNote,
    WeiboNoteComment,
)

_METRIC_TO_FIELD = {
    "likes": "like_count",
    "comments": "comment_count",
    "shares": "share_count",
    "collects": "collect_count",
    "replies": "reply_count",
}


@dataclass
class VectorSyncMapper:
    model: type[VectorSourceBase]
    mapping_config: ContentTableMapping | CommentTableMapping
    platform: str
    record_type: str

    def select_batch(self, limit: int, offset: int):
        return select(self.model).order_by(getattr(self.model, "id")).limit(limit).offset(offset)

    def to_document(self, row: Any) -> VectorDocument:
        return VectorDocument(
            doc_id=f"{self.platform}:{self.mapping_config.table_name}:{row.id}",
            platform=self.platform,
            source_table=self.mapping_config.table_name,
            mysql_pk=int(row.id),
            record_type=self.record_type,
            content=str(_read_attr(row, self.mapping_config.text_col)),
            published_at=str(_read_attr(row, self.mapping_config.published_at_col)),
            source_keyword=_source_keyword(self.mapping_config, row),
            **_extract_engagement(self.mapping_config, row),
        )


VECTOR_SYNC_REGISTRY: tuple[VectorSyncMapper, ...] = (
    VectorSyncMapper(DouyinAweme, PLATFORM_MAPPING["douyin"].content_mapping, "douyin", "post"),
    VectorSyncMapper(DouyinAwemeComment, PLATFORM_MAPPING["douyin"].comment_mapping, "douyin", "comment"),
    VectorSyncMapper(WeiboNote, PLATFORM_MAPPING["weibo"].content_mapping, "weibo", "post"),
    VectorSyncMapper(WeiboNoteComment, PLATFORM_MAPPING["weibo"].comment_mapping, "weibo", "comment"),
)


def _extract_engagement(mapping_config: ContentTableMapping | CommentTableMapping, row: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for metric, col_name in mapping_config.engagement_cols.items():
        field = _METRIC_TO_FIELD.get(metric)
        result[field] = _to_int(_read_attr(row, col_name))
    return result


def _read_attr(row: Any, attr_name: str) -> Any:
    return getattr(row, attr_name, None)


def _source_keyword(mapping_config: ContentTableMapping | CommentTableMapping, row: Any) -> str:
    source_keyword_col = getattr(mapping_config, "source_keyword_col", None)
    return str(_read_attr(row, source_keyword_col) or "") if source_keyword_col else ""


def _to_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
