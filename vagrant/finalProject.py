from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
# import manyRestaurants
app = Flask(__name__)
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Condition, Base

# New imports for state token
from flask import session as login_session
import random
import string

# IMPORTS FOR gconnect
from oauth2client.client import flow_from_clientsecrets  # creates a Flow object from a client_secrets.json file
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests # Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.

# if just do 'from manyRestaurants import Restaurant, session' and without the next 4 lines,get error
# 'SQLite objects created in a thread can only be used in that same thread'
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Therapeutic Foods Restaurants"


# The server creates anti-forgery state token and sends to the client
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/login2/')
def showLoginTwo():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login2.html", STATE=state)

@app.route('/login3/')
def showLogin3():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login3.html", STATE=state)

@app.route('/login4/')
def showLoginFour():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login4.html", STATE=state)

@app.route('/login5/')
def showLoginFive():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login5.html", STATE=state)

@app.route('/gconnect/', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']: # check what client sent is what server sent
        response = make_response(json.dumps('Invalid state parameter.'), 401)  #dumps:Serialize obj to a JSON formatted str
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain the one-time authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='', # creates a Flow object from a client_secrets.json file
                                             redirect_uri = 'postmessage')
        credentials = oauth_flow.step2_exchange(code)  # exchanges an authorization code for a Credentials object
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    # A Credentials object holds refresh and access tokens that authorize access
    # to a single user's data. These objects are applied to httplib2.Http objects to
    # authorize access.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1]) # loads:Deserialize to a Python object
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    # id_token: object, The identity of the resource owner.
    # 'Google ID Token's field (or claim) 'sub' is unique-identifier key for the user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output



@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurant=[i.serialize for i in restaurants])

@app.route('/restaurants/')
def showRestaurants():
	try:
		restaurants = session.query(Restaurant).all()
		return render_template('restaurants.html', restaurants=restaurants)
	except IOError as err:
		return "No restaurant, error:"
	finally:
		flash("This page will show all my restaurants")

@app.route('/restaurants/new/', methods=['POST','GET'])
def restaurantNew():
    if request.method == 'POST':
        myNewRestaurant = Restaurant(name=request.form['newName'])
        session.add(myNewRestaurant)
        session.commit()
        flash('New restaurant ' + myNewRestaurant.name+' has been created!')
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['POST','GET'])
def restaurantEdit(restaurant_id):
    if request.method == 'POST':
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        laRestaurant.name = request.form['newName']
        session.add(laRestaurant)
        session.commit()
        flash('The restaurant '+ laRestaurant.name+ ' has been edited!')
        return redirect(url_for('showRestaurants'))
    else:
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        return render_template('editRestaurant.html', restaurant_id=restaurant_id,restaurant=laRestaurant)

@app.route('/restaurants/<int:restaurant_id>/delete/',methods=['POST','GET'])
def restaurantDelete(restaurant_id):
    laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if(laRestaurant):
            session.delete(laRestaurant)
            session.commit()
            flash('Restaurant '+laRestaurant.name+' has been sadly deleted...')
            return redirect(url_for('showRestaurants'))
        else:
            return "no such restaurant found"  # TODO: send error message when no such restaurant
    else:
        return render_template('deleteRestaurant.html', restaurant_id=restaurant_id, restaurant=laRestaurant)

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
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        myNewMenu = MenuItem(name=request.form['newName'],
                             course=request.form['newCourse'],
                             description=request.form['newDescription'],
                             price=request.form['newPrice'],
                             restaurant_id=restaurant_id)
        session.add(myNewMenu)
        session.commit()
        flash('New menu ' + myNewMenu.name+' has been created!')
        return redirect(url_for('showMenus',restaurant_id=restaurant_id))
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
        return redirect(url_for('showMenus',restaurant_id=restaurant_id))
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
    	return redirect(url_for('showMenus',restaurant_id=restaurant_id))
    else:
    	return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id, menu=laMenu)

@app.route('/conditions/')
def showConditions():
    conditions = session.query(Condition).all()
    return render_template('conditions.html', conditions=conditions)

@app.route('/conditions/new/', methods=['POST','GET'])
def newCondition():
    if request.method == 'POST':
        condition = Condition(name=request.form['name'],
                              signs_and_symptoms=request.form['signs_and_symptoms']
                              )
        session.add(condition)
        session.commit()
        flash('the condition '+condition.name+' has been listed!')
        return redirect(url_for('showConditions'))
    else:
        return render_template('newCondition.html')

@app.route('/conditions/<int:condition_id>/menu/', methods=['POST','GET'])
def conditionMenus(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    myMenus = session.query(MenuItem).filter_by(condition_id=condition_id)
    return render_template('conditionMenus.html', condition=laCondition, menus=myMenus)

@app.route('/conditions/<int:condition_id>/menu/<int:menu_id>/', methods=['POST','GET'])
def linkMenuToCondition(condition_id,menu_id):
    return "recommended menu "+menu_id+" for condition "+condition_id

if __name__ == '__main__':
    # If you enable debug support the server will reload itself on code changes
    app.secret_key='super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)