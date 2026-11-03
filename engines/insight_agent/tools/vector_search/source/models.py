from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class VectorSourceBase(DeclarativeBase):
    pass


class DouyinAweme(VectorSourceBase):
    __tablename__ = "douyin_aweme"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str | None] = mapped_column(String)
    source_keyword: Mapped[str | None] = mapped_column(String)
    create_time: Mapped[int | None] = mapped_column(Integer)
    liked_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    share_count: Mapped[int | None] = mapped_column(Integer)
    collected_count: Mapped[int | None] = mapped_column(Integer)


class DouyinAwemeComment(VectorSourceBase):
    __tablename__ = "douyin_aweme_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str | None] = mapped_column(String)
    create_time: Mapped[int | None] = mapped_column(Integer)
    like_count: Mapped[int | None] = mapped_column(Integer)
    sub_comment_count: Mapped[int | None] = mapped_column(Integer)


class WeiboNote(VectorSourceBase):
    __tablename__ = "weibo_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str | None] = mapped_column(String)
    source_keyword: Mapped[str | None] = mapped_column(String)
    create_time: Mapped[int | None] = mapped_column(Integer)
    liked_count: Mapped[int | None] = mapped_column(Integer)
    comments_count: Mapped[int | None] = mapped_column(Integer)
    shared_count: Mapped[int | None] = mapped_column(Integer)


class WeiboNoteComment(VectorSourceBase):
    __tablename__ = "weibo_note_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str | None] = mapped_column(String)
    create_time: Mapped[int | None] = mapped_column(Integer)
    comment_like_count: Mapped[int | None] = mapped_column(Integer)
    sub_comment_count: Mapped[int | None] = mapped_column(Integer)
