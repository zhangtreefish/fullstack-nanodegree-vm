from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Condition, User, Base

engine = create_engine('sqlite:///restaurantmenuconditionuser.db')
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
print laRes

myFirstCondition = Condition(name='diabetes',signs_and_symptoms='thirst, fatigue, frequent urination, weight loss')
# link a menu to myFirstCondition
diabeticMenu1 = MenuItem(name='baked sweet potato',
                        description='sweet potato baked at 350 for 45 minutes, with skin',
                        price='$3.00',
                        course='vegetable',
                        restaurant=mySecondRestaurant)
session.add(diabeticMenu1)
session.commit()
myFirstCondition.suggested_menus.append(diabeticMenu1)
session.add(myFirstCondition)
session.commit()
laCon = session.query(Condition).all()
print laCon[0].suggested_menus[0].name

myFirstUser = User(name='treefish',email='zhangtreefish@yahoo.com', picture='')
session.add(myFirstUser)
session.commit()
myFirstUser.restaurants.append(myFirstRestaurant)
myFirstUser.conditions.append(myFirstCondition)
session.add(myFirstUser)
session.commit()

