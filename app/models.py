from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Recipes(Base):
    __tablename__ = "Рецепты"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    article = Column(String, nullable=False)
    ingredients = Column(String, nullable=False)
    steps = Column(String, nullable=False)

    category_id = Column(Integer, ForeignKey("Категории.id", ondelete="CASCADE"), nullable=False)
    category = relationship("Categories", back_populates='recipe')

    created_by_id = Column(Integer, ForeignKey('Пользователи.id', ondelete="CASCADE"), nullable=False)
    created_by = relationship("Users", back_populates='recipe')


class Categories(Base):
    __tablename__ = "Категории"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=False)

    recipe = relationship("Recipes", back_populates='category')


class Users(Base):
    __tablename__ = "Пользователи"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=False)

    recipe = relationship("Recipes", back_populates='created_by')
