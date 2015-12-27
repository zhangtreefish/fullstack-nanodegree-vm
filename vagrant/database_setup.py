#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    menus = relationship('MenuItem',back_populates='restaurant')

    def __repr__(self):
        return "<Restaurant(name='%s', description='%s')>" % (
                             self.name, self.description)

    @property
    def serialize(self):
        return {'name':self.name,
                'id':self.id
                }

association_table = Table('association',Base.metadata,
                          Column('condition_id', Integer, ForeignKey('condition.id')),
                          Column('menu_id', Integer, ForeignKey('menu_item.id'))
                          )


class Condition(Base):
    __tablename__ = 'condition'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    signs_and_symptoms = Column(String(250))
    suggested_menus = relationship('MenuItem',secondary=association_table, back_populates='conditions')


class MenuItem(Base):
    __tablename__ = 'menu_item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', back_populates='menus')
    conditions = relationship('Condition', secondary=association_table, back_populates='suggested_menus')

# Restaurant.menu_item = relationship('MenuItem',order_by=MenuItem.id,back_populates='restaurant')

    @property
    def serialize(self):
        return {'name':self.name,
                'course':self.course,
                'description':self.description,
                'price':self.price,
                'id':self.id,
                'restaurant_id':self.restaurant_id,
             #    'condition_id':self.condition_id
             #   'restaurant':self.restaurant  # 'restaurant is not serializable'
                }

engine = create_engine('sqlite:///restaurantmenu.db', echo=True)

# use MetaData to issue CREATE TABLE statements to the database for all tables
Base.metadata.create_all(engine)
