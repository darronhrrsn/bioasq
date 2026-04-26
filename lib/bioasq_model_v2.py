from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class Batch(Base):
    __tablename__ = "batch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    file_name: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    file_sha256: Mapped[Optional[str]] = mapped_column(Text)

    loaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    entry_batch_models: Mapped[list["EntryBatchModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batch.id", ondelete="RESTRICT"),
        nullable=False,
    )

    bioasq_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(Text)
    body_extra: Mapped[Optional[str]] = mapped_column(Text)
    type_extra: Mapped[Optional[str]] = mapped_column(Text)
    duplicate_tmp_json: Mapped[Optional[str]] = mapped_column(Text)

    batch: Mapped["Batch"] = relationship(back_populates="questions")

    documents: Mapped[list["QuestionDocument"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    snippets: Mapped[list["QuestionSnippet"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    ideal_answers: Mapped[list["QuestionIdealAnswer"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    exact_answers: Mapped[list["QuestionExactAnswer"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="question",
        passive_deletes=True,
    )


Index("idx_question_batch_id", Question.batch_id)
Index("idx_question_bioasq_id", Question.bioasq_id)


class QuestionDocument(Base):
    __tablename__ = "question_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )

    document_url: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="documents")

    __table_args__ = (
        Index("idx_question_document_question_id", "question_id"),
        UniqueConstraint(
            "question_id",
            "ordinal",
            name="uq_question_document_question_id_ordinal",
        ),
        UniqueConstraint(
            "question_id",
            "document_url",
            name="uq_question_document_question_id_document_url",
        ),
    )


class QuestionSnippet(Base):
    __tablename__ = "question_snippet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )

    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    document_url: Mapped[Optional[str]] = mapped_column(Text)
    begin_section: Mapped[Optional[str]] = mapped_column(Text)
    end_section: Mapped[Optional[str]] = mapped_column(Text)
    offset_in_begin_section: Mapped[Optional[int]] = mapped_column(Integer)
    offset_in_end_section: Mapped[Optional[int]] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="snippets")

    __table_args__ = (
        Index("idx_question_snippet_question_id", "question_id"),
        UniqueConstraint(
            "question_id",
            "ordinal",
            name="uq_question_snippet_question_id_ordinal",
        ),
    )


class QuestionIdealAnswer(Base):
    __tablename__ = "question_ideal_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )

    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="ideal_answers")

    __table_args__ = (
        Index("idx_question_ideal_answer_question_id", "question_id"),
        UniqueConstraint(
            "question_id",
            "ordinal",
            name="uq_question_ideal_answer_question_id_ordinal",
        ),
    )


class QuestionExactAnswer(Base):
    __tablename__ = "question_exact_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"),
        nullable=False,
    )

    answer_group: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    answer_item: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="exact_answers")

    __table_args__ = (
        Index("idx_question_exact_answer_question_id", "question_id"),
        UniqueConstraint(
            "question_id",
            "answer_group",
            "answer_item",
            name="uq_question_exact_answer_question_group_item",
        ),
    )


class Model(Base):
    __tablename__ = "model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    label: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    provider: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    entry_batch_models: Mapped[list["EntryBatchModel"]] = relationship(
        back_populates="model",
        passive_deletes=True,
    )


Index("idx_model_label", Model.label)
Index("idx_model_model_id", Model.model_id)


class Entry(Base):
    __tablename__ = "entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    label: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    entry_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="entry",
        server_default=text("'entry'"),
    )

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    entry_batch_models: Mapped[list["EntryBatchModel"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="entry",
        passive_deletes=True,
    )


Index("idx_entry_label", Entry.label)


class EntryBatchModel(Base):
    __tablename__ = "entry_batch_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entry.id", ondelete="CASCADE"),
        nullable=False,
    )

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batch.id", ondelete="CASCADE"),
        nullable=False,
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey("model.id", ondelete="RESTRICT"),
        nullable=False,
    )

    ordinal: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )

    role: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="primary",
        server_default=text("'primary'"),
    )

    usage_scope: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="all",
        server_default=text("'all'"),
    )

    prompt_variant: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    entry: Mapped["Entry"] = relationship(back_populates="entry_batch_models")
    batch: Mapped["Batch"] = relationship(back_populates="entry_batch_models")
    model: Mapped["Model"] = relationship(back_populates="entry_batch_models")

    __table_args__ = (
        Index("idx_entry_batch_model_entry_id", "entry_id"),
        Index("idx_entry_batch_model_batch_id", "batch_id"),
        Index("idx_entry_batch_model_model_id", "model_id"),
        UniqueConstraint(
            "entry_id",
            "batch_id",
            "ordinal",
            name="uq_entry_batch_model_entry_batch_ordinal",
        ),
        UniqueConstraint(
            "entry_id",
            "batch_id",
            "model_id",
            "role",
            "usage_scope",
            "prompt_variant",
            name="uq_entry_batch_model_entry_batch_model_role_scope_prompt",
        ),
    )


class Judge(Base):
    __tablename__ = "judge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    label: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    load_extended: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    judge_scores: Mapped[list["JudgeScore"]] = relationship(
        back_populates="judge",
        passive_deletes=True,
    )


Index("idx_judge_label", Judge.label)


class Run(Base):
    __tablename__ = "run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    label: Mapped[Optional[str]] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gold_dir: Mapped[Optional[str]] = mapped_column(Text)
    input_glob: Mapped[Optional[str]] = mapped_column(Text)
    input_file_name: Mapped[Optional[str]] = mapped_column(Text)
    file_prefix: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class Prediction(Base):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"),
        nullable=False,
    )

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entry.id", ondelete="RESTRICT"),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="RESTRICT"),
        nullable=False,
    )

    prediction_raw: Mapped[Optional[str]] = mapped_column(Text)
    prediction_exact: Mapped[Optional[str]] = mapped_column(Text)
    prediction_ideal: Mapped[Optional[str]] = mapped_column(Text)
    selected_snippet_json: Mapped[Optional[str]] = mapped_column(Text)

    generation_seconds: Mapped[Optional[float]] = mapped_column(Float)
    generated_in: Mapped[Optional[float]] = mapped_column(Float)
    tokens_generated: Mapped[Optional[int]] = mapped_column(Integer)
    gpu_type: Mapped[Optional[str]] = mapped_column(Text)

    answer_char_count: Mapped[Optional[int]] = mapped_column(Integer)
    answer_token_count: Mapped[Optional[int]] = mapped_column(Integer)
    sentence_count: Mapped[Optional[int]] = mapped_column(Integer)
    avg_sentence_length: Mapped[Optional[float]] = mapped_column(Float)
    type_token_ratio: Mapped[Optional[float]] = mapped_column(Float)
    repeated_bigram_rate: Mapped[Optional[float]] = mapped_column(Float)
    repeated_trigram_rate: Mapped[Optional[float]] = mapped_column(Float)
    duplicate_sentence_rate: Mapped[Optional[float]] = mapped_column(Float)
    biomed_entity_count: Mapped[Optional[int]] = mapped_column(Integer)
    unique_biomed_entity_count: Mapped[Optional[int]] = mapped_column(Integer)
    biomed_entity_density: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    run: Mapped["Run"] = relationship(back_populates="predictions")
    entry: Mapped["Entry"] = relationship(back_populates="predictions")
    question: Mapped["Question"] = relationship(back_populates="predictions")

    judge_scores: Mapped[list["JudgeScore"]] = relationship(
        back_populates="prediction",
        cascade="all, delete-orphan",
    )

    rouge_score: Mapped[Optional["RougeScore"]] = relationship(
        back_populates="prediction",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_prediction_run_id", "run_id"),
        Index("idx_prediction_entry_id", "entry_id"),
        Index("idx_prediction_question_id", "question_id"),
        UniqueConstraint(
            "run_id",
            "entry_id",
            "question_id",
            name="uq_prediction_run_entry_question",
        ),
    )


class JudgeScore(Base):
    __tablename__ = "judge_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("prediction.id", ondelete="CASCADE"),
        nullable=False,
    )

    judge_id: Mapped[int] = mapped_column(
        ForeignKey("judge.id", ondelete="RESTRICT"),
        nullable=False,
    )

    sample_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    information_recall: Mapped[float] = mapped_column(Float, nullable=False)
    information_precision: Mapped[float] = mapped_column(Float, nullable=False)
    information_repetition: Mapped[float] = mapped_column(Float, nullable=False)
    readability: Mapped[float] = mapped_column(Float, nullable=False)

    judge_seconds: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    prediction: Mapped["Prediction"] = relationship(back_populates="judge_scores")
    judge: Mapped["Judge"] = relationship(back_populates="judge_scores")

    __table_args__ = (
        CheckConstraint(
            "information_recall >= 1.0 AND information_recall <= 5.0",
            name="ck_judge_score_information_recall",
        ),
        CheckConstraint(
            "information_precision >= 1.0 AND information_precision <= 5.0",
            name="ck_judge_score_information_precision",
        ),
        CheckConstraint(
            "information_repetition >= 1.0 AND information_repetition <= 5.0",
            name="ck_judge_score_information_repetition",
        ),
        CheckConstraint(
            "readability >= 1.0 AND readability <= 5.0",
            name="ck_judge_score_readability",
        ),
        Index("idx_judge_score_prediction_id", "prediction_id"),
        Index("idx_judge_score_judge_id", "judge_id"),
        UniqueConstraint(
            "prediction_id",
            "judge_id",
            "sample_index",
            name="uq_judge_score_prediction_judge_sample",
        ),
    )


class RougeScore(Base):
    __tablename__ = "rouge_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("prediction.id", ondelete="CASCADE"),
        nullable=False,
    )

    rouge_2_precision: Mapped[Optional[float]] = mapped_column(Float)
    rouge_2_recall: Mapped[Optional[float]] = mapped_column(Float)
    rouge_2_f1: Mapped[Optional[float]] = mapped_column(Float)

    rouge_su4_precision: Mapped[Optional[float]] = mapped_column(Float)
    rouge_su4_recall: Mapped[Optional[float]] = mapped_column(Float)
    rouge_su4_f1: Mapped[Optional[float]] = mapped_column(Float)

    rouge_seconds: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    prediction: Mapped["Prediction"] = relationship(back_populates="rouge_score")

    __table_args__ = (
        Index("idx_rouge_score_prediction_id", "prediction_id"),
        UniqueConstraint(
            "prediction_id",
            name="uq_rouge_score_prediction_id",
        ),
    )


def make_engine(db_path: str, echo: bool = False):
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=echo,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def make_session_factory(db_path: str, echo: bool = False):
    engine = make_engine(db_path=db_path, echo=echo)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )


def create_schema(db_path: str, echo: bool = False):
    engine = make_engine(db_path=db_path, echo=echo)
    Base.metadata.create_all(engine)
    return engine


def drop_schema(db_path: str, echo: bool = False):
    engine = make_engine(db_path=db_path, echo=echo)
    Base.metadata.drop_all(engine)
    return engine