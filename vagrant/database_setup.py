import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        return {'name':self.name,
                'id':self.id
                }


class Condition(Base):
    __tablename__ = 'condition'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    signs_and_symptoms = Column(String(250))


class MenuItem(Base):
    __tablename__ = 'menu_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship(Restaurant)
    condition_id = Column(Integer, ForeignKey('condition.id'))
    condition = relationship(Condition)


    @property
    def serialize(self):
        return {'name':self.name,
                'course':self.course,
                'description':self.description,
                'price':self.price,
                'id':self.id,
                'restaurant_id':self.restaurant_id,
             #   'restaurant':self.restaurant  # 'restaurant is not serializable'
                }

engine = create_engine('sqlite:///restaurantmenu.db')


Base.metadata.create_all(engine)
