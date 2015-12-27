from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Condition, Base

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

myFirstRestaurant = Restaurant(name='steam', description='all things steamed')
mySecondRestaurant = Restaurant(name='3Fs',description='that features fiber, fitness, and fluid')
myThirdRestaurant = Restaurant(name='Eden',description='out of your dream garden')
session.add(myFirstRestaurant)
session.add(mySecondRestaurant)
session.add(myThirdRestaurant)
session.commit()
restaurant_list=session.query(Restaurant).all()
print session.query(Restaurant).first().name

# will not work if restaurant='myFirstRestaurant'
myFirstMenu = MenuItem(name='jade',
	                   description='daikon steamed to a luscious texture',
	                   price='$2.50',
	                   course='vegetable',
                       restaurant=myFirstRestaurant)
mySecondMenu = MenuItem(name='FragrantSnow',
                        description='sweet rice flour balls encasing honey-infused sweet olive blossoms and coconut oil',
                        price='$4.00',
                        course='dessert',
                        restaurant=myFirstRestaurant)
session.add(myFirstMenu)
session.add(mySecondMenu)
session.commit()
laRes = session.query(MenuItem).first().name
print session.query(MenuItem).first().name

myFirstCondition = Condition(name='diabetes',signs_and_symptoms='thirst, fatigue, frequent urination, weight loss')
session.add(myFirstCondition)
session.commit()

myFirstCondition.suggested_menus.append(myFirstMenu)
session.add(myFirstCondition)
session.commit()
