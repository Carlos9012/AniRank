import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MediaFormat(str, enum.Enum):
    TV = "TV"
    TV_SHORT = "TV_SHORT"
    MOVIE = "MOVIE"
    OVA = "OVA"
    SPECIAL = "SPECIAL"
    ONA = "ONA"


class MediaSource(str, enum.Enum):
    ORIGINAL = "ORIGINAL"
    ANIME = "ANIME"


class WatchStatus(str, enum.Enum):
    watching = "watching"
    completed = "completed"
    planned = "planned"
    dropped = "dropped"


class AiringStatus(str, enum.Enum):
    finished = "FINISHED"
    releasing = "RELEASING"
    not_yet_released = "NOT_YET_RELEASED"
    cancelled = "CANCELLED"
    hiatus = "HIATUS"


# Tabela associativa para many-to-many entre Anime e Genre
anime_genre_association = Table(
    "anime_genres",
    Base.metadata,
    Column(
        "anime_id",
        Integer,
        ForeignKey("animes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    # Relacionamentos
    anime_statuses = relationship(
        "UserAnimeStatus", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    # Relacionamento many-to-many com Anime
    animes = relationship(
        "Anime", secondary=anime_genre_association, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Anime(Base):
    __tablename__ = "animes"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(
        Integer, unique=True, index=True, nullable=False
    )  # id do AniList
    title = Column(String(500), nullable=False, index=True)
    synopsis = Column(Text, nullable=True)
    episodes = Column(Integer, nullable=True)
    release_year = Column(Integer, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    airing_status = Column(Enum(AiringStatus), nullable=True)
    format = Column(Enum(MediaFormat), nullable=True)
    source = Column(Enum(MediaSource), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    genres = relationship(
        "Genre", secondary=anime_genre_association, back_populates="animes"
    )
    user_statuses = relationship(
        "UserAnimeStatus", back_populates="anime", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Anime(id={self.id}, title='{self.title[:30]}...')>"


class UserAnimeStatus(Base):
    __tablename__ = "user_anime_status"
    __table_args__ = (UniqueConstraint("user_id", "anime_id", name="uq_user_anime"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    anime_id = Column(
        Integer, ForeignKey("animes.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(Enum(WatchStatus), nullable=False, default=WatchStatus.planned)
    score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    user = relationship("User", back_populates="anime_statuses")
    anime = relationship("Anime", back_populates="user_statuses")

    def __repr__(self):
        return f"<UserAnimeStatus(user_id={self.user_id}, anime_id={self.anime_id}, status='{self.status}')>"
