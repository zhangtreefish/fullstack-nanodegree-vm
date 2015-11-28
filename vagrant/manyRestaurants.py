from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Base

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

myFirstRestaurant = Restaurant(name='steam')
mySecondRestaurant = Restaurant(name='3Fs')
myThirdRestaurant = Restaurant(name='Eden')
session.add(myFirstRestaurant)
session.add(mySecondRestaurant)
session.add(myThirdRestaurant)
session.commit()
restaurant_list=session.query(Restaurant).all()
print session.query(Restaurant).first().name

# will not work if restaurant='myFirstRestaurant'
myFirstMenu = MenuItem(name='jade', description='daikon steamed to a luscious \
                     texture', price='$2.50', course='vegetable', \
                     restaurant=myFirstRestaurant)
session.add(myFirstMenu)
session.commit()
laRes = session.query(MenuItem).first().name
print session.query(MenuItem).first().name
