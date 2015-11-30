from flask import Flask
# import manyRestaurants
app = Flask(__name__)
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Base
# if just do 'from manyRestaurants import Restaurant, session' and without the next 4 lines,get error
# 'SQLite objects created in a thread can only be used in that same thread'
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    # without one(), gets error 'AttributeError: 'Query' object has no attribute 'id''
    laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    myMenus = session.query(MenuItem).filter_by(restaurant_id=laRestaurant.id)
    output = 'Menu of My Restaurant '
    output += string.capwords(laRestaurant.name)
    output += '</br>'
    for menu in myMenus:
        output += menu.course
        output += '</br>'
        output += menu.name
        output += '</br>'
        output += menu.description
        output += '</br>'
        output += menu.price
        output += '</br>'
        output += '</br>'

    return output
# Task 1: Create route for newMenuItem function here

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/new/')
def newMenuItem(restaurant_id):
    return "page to create a new menu item. Task 1 complete!"

# Task 2: Create route for editMenuItem function here TODO

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/')
def editMenuItem(restaurant_id, menu_id):
    return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here TODO

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/')
def deleteMenuItem(restaurant_id, menu_id):
    return "page to delete a menu item. Task 3 complete!"

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)