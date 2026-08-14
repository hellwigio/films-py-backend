"""SQLAlchemy-модели таблиц фильмов и категорий Sakila."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from films.database import Base

film_category = Table(
    "film_category",
    Base.metadata,
    Column("film_id", ForeignKey("film.film_id"), primary_key=True),
    Column("category_id", ForeignKey("category.category_id"), primary_key=True),
)


class Film(Base):
    """Фильм из таблицы Sakila ``film``."""

    __tablename__ = "film"

    id: Mapped[int] = mapped_column("film_id", primary_key=True)
    title: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rental_duration: Mapped[int] = mapped_column(Integer)
    rental_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replacement_cost: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    special_features: Mapped[str | None] = mapped_column(String(255), nullable=True)

    categories: Mapped[list[Category]] = relationship(
        secondary=film_category,
        back_populates="films",
    )

    @property
    def genres(self) -> list[str]:
        """Вернуть названия связанных категорий фильма."""

        return [category.name for category in self.categories]

    @property
    def features(self) -> list[str]:
        """Преобразовать строку специальных возможностей в список."""

        if not self.special_features:
            return []

        return [
            feature.strip()
            for feature in self.special_features.split(",")
            if feature.strip()
        ]


class Category(Base):
    """Категория фильма из таблицы Sakila ``category``."""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column("category_id", primary_key=True)
    name: Mapped[str] = mapped_column(String(25), index=True)

    films: Mapped[list[Film]] = relationship(
        secondary=film_category,
        back_populates="categories",
    )
