from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
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

@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurant=[i.serialize for i in restaurants])

@app.route('/restaurants/')
def showRestaurants():
	return "This page will show all my restaurants"

@app.route('/restaurants/new')
def restaurantNew():
	return "This page will make a restaurant"

@app.route('/restaurants/<int:restaurant_id>/edit/')
def restaurantEdit(restaurant_id):
	laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	return "This page will edit restaurant %s" % laRestaurant.name

@app.route('/restaurants/<int:restaurant_id>/delete/')
def restaurantDelete(restaurant_id):
	laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	return "This page will delete restaurant %s" % laRestaurant.name

@app.route('/restaurants/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    menus = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    return jsonify(menuItem=[i.serialize for i in menus])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def menuJSON(restaurant_id, menu_id):
    menu = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(menuItem=menu.serialize)


# route() decorator to tell Flask what URL should trigger method
@app.route('/')
@app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def showMenus(restaurant_id):
    # without one(), gets error 'AttributeError: 'Query' object has no attribute 'id''
    laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    myMenus = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    return render_template('menu.html', restaurant=laRestaurant, menus=myMenus)

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET','POST'])
def newMenu(restaurant_id):
    if request.method == 'POST':
        myNewMenu = MenuItem(name=request.form['newName'],
                             course=request.form['newCourse'],
                             description=request.form['newDescription'],
                             price=request.form['newPrice'],
                             restaurant_id=restaurant_id)
        # print ('aha',request.form['newMenu'])
        session.add(myNewMenu)
        session.commit()
        flash('New menu ' + myNewMenu.name+' has been created!')
        return redirect(url_for('restaurantMenu',restaurant_id=restaurant_id))
    else:
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        return render_template('newMenuItem.html',restaurant_id=restaurant_id, restaurant=laRestaurant)

# Task 2: Create route for editMenuItem function here TODO

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenu(restaurant_id, menu_id):
    laMenu = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
    	laMenu.name = request.form['newName']
    	laMenu.course = request.form['newCourse']
    	laMenu.description = request.form['newDescription']
    	laMenu.price = request.form['newPrice']
    	session.add(laMenu)
        session.commit()
        flash('The menu '+laMenu.name + ' has been edited!')
        return redirect(url_for('restaurantMenu',restaurant_id=restaurant_id))
    else:
    	laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        return render_template('editMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id,restaurant=laRestaurant, menu=laMenu)

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET','POST'])
def deleteMenu(restaurant_id, menu_id):
    laMenu = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
    	name =  laMenu.name
    	session.delete(laMenu)
    	session.commit()
    	flash('the menu '+name+' has been deleted!')
    	return redirect(url_for('restaurantMenu',restaurant_id=restaurant_id))
    else:
    	return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id, menu=laMenu)

if __name__ == '__main__':
    # If you enable debug support the server will reload itself on code changes
    app.secret_key='super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)