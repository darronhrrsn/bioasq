from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    create_engine,
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
        DateTime, nullable=False, default=datetime.utcnow
    )

    questions: Mapped[list[Question]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batch.id", ondelete="RESTRICT"), nullable=False
    )
    bioasq_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(Text)
    body_extra: Mapped[Optional[str]] = mapped_column(Text)
    type_extra: Mapped[Optional[str]] = mapped_column(Text)
    duplicate_tmp_json: Mapped[Optional[str]] = mapped_column(Text)

    batch: Mapped[Batch] = relationship(back_populates="questions")
    documents: Mapped[list[QuestionDocument]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    snippets: Mapped[list[QuestionSnippet]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    ideal_answers: Mapped[list[QuestionIdealAnswer]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    exact_answers: Mapped[list[QuestionExactAnswer]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    predictions: Mapped[list[Prediction]] = relationship(back_populates="question")
    judge_scores: Mapped[list[JudgeScore]] = relationship(back_populates="question")
    rouge_scores: Mapped[list[RougeScore]] = relationship(back_populates="question")


Index("idx_question_batch_id", Question.batch_id)
Index("idx_question_bioasq_id", Question.bioasq_id)


class QuestionDocument(Base):
    __tablename__ = "question_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    document_url: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped[Question] = relationship(back_populates="documents")

    __table_args__ = (
        Index("idx_question_document_question_id", "question_id"),
        Index(
            "uq_question_document_question_id_ordinal",
            "question_id",
            "ordinal",
            unique=True,
        ),
        Index(
            "uq_question_document_question_id_document_url",
            "question_id",
            "document_url",
            unique=True,
        ),
    )


class QuestionSnippet(Base):
    __tablename__ = "question_snippet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    document_url: Mapped[Optional[str]] = mapped_column(Text)
    begin_section: Mapped[Optional[str]] = mapped_column(Text)
    end_section: Mapped[Optional[str]] = mapped_column(Text)
    offset_in_begin_section: Mapped[Optional[int]] = mapped_column(Integer)
    offset_in_end_section: Mapped[Optional[int]] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped[Question] = relationship(back_populates="snippets")

    __table_args__ = (
        Index("idx_question_snippet_question_id", "question_id"),
        Index(
            "uq_question_snippet_question_id_ordinal",
            "question_id",
            "ordinal",
            unique=True,
        ),
    )


class QuestionIdealAnswer(Base):
    __tablename__ = "question_ideal_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped[Question] = relationship(back_populates="ideal_answers")

    __table_args__ = (
        Index("idx_question_ideal_answer_question_id", "question_id"),
        Index(
            "uq_question_ideal_answer_question_id_ordinal",
            "question_id",
            "ordinal",
            unique=True,
        ),
    )


class QuestionExactAnswer(Base):
    __tablename__ = "question_exact_answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    answer_group: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answer_item: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    question: Mapped[Question] = relationship(back_populates="exact_answers")

    __table_args__ = (
        Index("idx_question_exact_answer_question_id", "question_id"),
        Index(
            "uq_question_exact_answer_question_group_item",
            "question_id",
            "answer_group",
            "answer_item",
            unique=True,
        ),
    )


class Entry(Base):
    __tablename__ = "entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    entry_type: Mapped[str] = mapped_column(Text, nullable=False, default="entry")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    predictions: Mapped[list[Prediction]] = relationship(back_populates="entry")
    judge_scores: Mapped[list[JudgeScore]] = relationship(back_populates="entry")
    rouge_scores: Mapped[list[RougeScore]] = relationship(back_populates="entry")

    __mapper_args__ = {
        "polymorphic_on": entry_type,
        "polymorphic_identity": "entry",
    }


class EPEntry(Entry):
    __mapper_args__ = {"polymorphic_identity": "ep"}


class LasigeBioTMEntry(Entry):
    __mapper_args__ = {"polymorphic_identity": "lasigebiotm"}


class ARBEntry(Entry):
    __mapper_args__ = {"polymorphic_identity": "arb"}


class Judge(Base):
    __tablename__ = "judge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    model_id: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    judge_scores: Mapped[list[JudgeScore]] = relationship(back_populates="judge")


class Run(Base):
    __tablename__ = "run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gold_dir: Mapped[Optional[str]] = mapped_column(Text)
    input_glob: Mapped[Optional[str]] = mapped_column(Text)
    input_file_name: Mapped[Optional[str]] = mapped_column(Text)
    file_prefix: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    predictions: Mapped[list[Prediction]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    judge_scores: Mapped[list[JudgeScore]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    rouge_scores: Mapped[list[RougeScore]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Prediction(Base):
    __tablename__ = "prediction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"), nullable=False
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entry.id", ondelete="RESTRICT"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="RESTRICT"), nullable=False
    )
    prediction_raw: Mapped[Optional[str]] = mapped_column(Text)
    prediction_exact: Mapped[Optional[str]] = mapped_column(Text)
    prediction_ideal: Mapped[Optional[str]] = mapped_column(Text)
    selected_snippet_json: Mapped[Optional[str]] = mapped_column(Text)
    generation_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    run: Mapped[Run] = relationship(back_populates="predictions")
    entry: Mapped[Entry] = relationship(back_populates="predictions")
    question: Mapped[Question] = relationship(back_populates="predictions")
    judge_scores: Mapped[list[JudgeScore]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )
    rouge_scores: Mapped[list[RougeScore]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_prediction_run_id", "run_id"),
        Index("idx_prediction_entry_id", "entry_id"),
        Index("idx_prediction_question_id", "question_id"),
        Index(
            "uq_prediction_run_entry_question",
            "run_id",
            "entry_id",
            "question_id",
            unique=True,
        ),
    )


class JudgeScore(Base):
    __tablename__ = "judge_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"), nullable=False
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entry.id", ondelete="RESTRICT"), nullable=False
    )
    judge_id: Mapped[int] = mapped_column(
        ForeignKey("judge.id", ondelete="RESTRICT"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="RESTRICT"), nullable=False
    )
    information_recall: Mapped[float] = mapped_column(Float, nullable=False)
    information_precision: Mapped[float] = mapped_column(Float, nullable=False)
    information_repetition: Mapped[float] = mapped_column(Float, nullable=False)
    readability: Mapped[float] = mapped_column(Float, nullable=False)
    judge_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    run: Mapped[Run] = relationship(back_populates="judge_scores")
    entry: Mapped[Entry] = relationship(back_populates="judge_scores")
    judge: Mapped[Judge] = relationship(back_populates="judge_scores")
    question: Mapped[Question] = relationship(back_populates="judge_scores")
    prediction: Mapped[Prediction] = relationship(
        back_populates="judge_scores",
        primaryjoin=(
            "and_(JudgeScore.run_id == Prediction.run_id, "
            "JudgeScore.entry_id == Prediction.entry_id, "
            "JudgeScore.question_id == Prediction.question_id)"
        ),
        foreign_keys=lambda: [JudgeScore.run_id, JudgeScore.entry_id, JudgeScore.question_id],
    )

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
        ForeignKeyConstraint(
            ["run_id", "entry_id", "question_id"],
            ["prediction.run_id", "prediction.entry_id", "prediction.question_id"],
            ondelete="CASCADE",
        ),
        Index("idx_judge_score_run_id", "run_id"),
        Index("idx_judge_score_entry_id", "entry_id"),
        Index("idx_judge_score_judge_id", "judge_id"),
        Index("idx_judge_score_question_id", "question_id"),
        Index(
            "uq_judge_score_run_entry_judge_question",
            "run_id",
            "entry_id",
            "judge_id",
            "question_id",
            unique=True,
        ),
    )


class RougeScore(Base):
    __tablename__ = "rouge_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("run.id", ondelete="CASCADE"), nullable=False
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entry.id", ondelete="RESTRICT"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="RESTRICT"), nullable=False
    )
    rouge_2_precision: Mapped[Optional[float]] = mapped_column(Float)
    rouge_2_recall: Mapped[Optional[float]] = mapped_column(Float)
    rouge_2_f1: Mapped[Optional[float]] = mapped_column(Float)
    rouge_su4_precision: Mapped[Optional[float]] = mapped_column(Float)
    rouge_su4_recall: Mapped[Optional[float]] = mapped_column(Float)
    rouge_su4_f1: Mapped[Optional[float]] = mapped_column(Float)
    rouge_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    run: Mapped[Run] = relationship(back_populates="rouge_scores")
    entry: Mapped[Entry] = relationship(back_populates="rouge_scores")
    question: Mapped[Question] = relationship(back_populates="rouge_scores")
    prediction: Mapped[Prediction] = relationship(
        back_populates="rouge_scores",
        primaryjoin=(
            "and_(RougeScore.run_id == Prediction.run_id, "
            "RougeScore.entry_id == Prediction.entry_id, "
            "RougeScore.question_id == Prediction.question_id)"
        ),
        foreign_keys=lambda: [RougeScore.run_id, RougeScore.entry_id, RougeScore.question_id],
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["run_id", "entry_id", "question_id"],
            ["prediction.run_id", "prediction.entry_id", "prediction.question_id"],
            ondelete="CASCADE",
        ),
        Index("idx_rouge_score_run_id", "run_id"),
        Index("idx_rouge_score_entry_id", "entry_id"),
        Index("idx_rouge_score_question_id", "question_id"),
        Index(
            "uq_rouge_score_run_entry_question",
            "run_id",
            "entry_id",
            "question_id",
            unique=True,
        ),
    )


def make_engine(db_path: str, echo: bool = False):
    return create_engine(f"sqlite:///{db_path}", echo=echo, future=True)


def make_session_factory(db_path: str, echo: bool = False):
    engine = make_engine(db_path=db_path, echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)