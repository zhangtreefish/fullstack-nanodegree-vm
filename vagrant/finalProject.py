from flask import Flask, render_template, url_for, request, redirect, flash
from flask import jsonify, make_response
import string
import random
import json
import httplib2
import requests
# import feedparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from oauth2client import client, crypt
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from database_setup import Restaurant, MenuItem, Condition, Base, User, engine
from functools import wraps
from xml.etree.ElementTree import Element, SubElement
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from os import linesep
# if just do 'from manyRestaurants import Restaurant, session' and without the
# next 2 lines,get error 'SQLite objects created in a thread can only be used
# in that same thread'
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

G_CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Therapeutic Foods Restaurants"


def createUser(login_session):
    """generator of user if the user is in session(i.e. logged in)"""
    # first check if user already present in users table
    user = session.query(User).filter_by(email=login_session['email']).first()
    if user is None:
        newUser = User(name=login_session['username'],
                       email=login_session['email'],
                       picture=login_session['picture']  # no need to add id
                       )
        session.add(newUser)
        session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    """identifying the user with certain user_id"""

    user = session.query(User).filter_by(id=user_id).one()
    print "user:", user
    return user


def getUserId(email):
    """identifying the user_id with the user's email"""

    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# for use in conjunction to restaurantsXml()
def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")# The server creates anti-forgery state token and sends to the client


@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route('/gconnect/', methods=['POST'])
def gconnect():
    # Validate state token:check what client sent is what server sent
    if request.args.get('state') != login_session['state']:
        return jsonify(message='Invalid state parameter.'), 401
    # Obtain the one-time authorization code from the authorization server
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        # flow_from_cl:creates a Flow object from the json file
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='',
                                             redirect_uri='postmessage')
        # exchanges an authorization code for a Credentials object
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        return jsonify(message='Failed to upgrade the authorization code.'),\
                        401

    # Check that the access token is valid.
    # A Credentials object holds refresh and access tokens that authorize
    # access to a single user's data. These objects are applied to httplib2
    # .Http objects to authorize access.
    print credentials
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    # loads:Deserialize to a Python object
    g_result = json.loads(h.request(url, 'GET')[1])
    # get(): return a value for given key;if unavail. ret. default None.
    if g_result.get('error') is not None:
        # either do the following 3 lines, or use jsonify
        # response = make_response(json.dumps(result.get('error')), 500)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return jsonify(message=g_result.get('error')), 500

    # Verify that the access token is used for the intended user.
    # id_token: object, the identity of the resource owner.
    # 'Google ID Token's field (or claim) 'sub' is unique-identifier key for
    # the user.
    gplus_id = credentials.id_token['sub']
    if g_result['user_id'] != gplus_id:
        return jsonify(message="Token's user ID doesn't match given user \
                        ID."), 401

    # Verify that the access token is valid for this app.
    if g_result['issued_to'] != G_CLIENT_ID:
        return jsonify(message="Token's client ID does not match app's."), 401

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        return jsonify(message='Current user is already connected.'), 200

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = credentials.access_token

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    # Requests is an Apache2 Licensed HTTP library, written in Python
    # for human beans.
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # check to see if user exist
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, User'
    output += str(login_session['user_id'])
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '">'
    flash("you are now logged in as %s" % login_session['username'], 'message')
    print "done gconnect!"
    return output


@app.route('/gdisconnect/')
def gdisconnect():
    # Only a connected user needs to do this
    credentials = login_session.get('credentials')
    if credentials is None:
        return jsonify(message='Why, current user not connected.'), 401

    # Execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')
    # TODO: why 200 means to clear cache while'200' not
    # reset the user's session
    if result[0]['status'] == 200:
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        del login_session['user_id']
        return jsonify(message='User successfully disconnected.'), 200
    else:
        return jsonify(message='Failed to revoke token for given user.'), 400

# TODO create user if have not yet
@app.route('/fbconnect/', methods=['POST'])
def fbconnect():
    # Validate state token:# check what client sent is what server sent
    if request.args.get('state') != login_session['state']:
        # dumps:Serialize obj to a JSON formatted str
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain the one-time authorization code from authorization server
    access_token = request.data
    # print 'fb access_token:',access_token
    app_info = json.loads(open('fb_client_secrets.json', 'r').read())
    # print app_info.to_json() # why print not working?
    app_id = app_info['web']['app_id']
    app_secret = app_info['web']['app_secret']
    token_url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # # try imgur
    # h = httplib2.Http()
    # imgru_url = 'https://api.imgur.com/3/album/0/images'
    # img_result = h.request(url, 'GET')[1]
    # print 'IMAGE:', img_result

    token = result.split("&")[0]
    info_url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    data = json.loads(h.request(info_url, 'GET')[1])
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    pic_url = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0' % token
    h = httplib2.Http()
    pic = json.loads(h.request(pic_url, 'GET')[1])
    login_session['picture'] = pic['data']['url']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome'
    # output += str(login_session['user_id'])
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '">'
    flash("you are now logged in as %s" % login_session['username'], 'message')
    return output


@app.route('/fbdisconnect/')
def fbdisconnect():
    # Execute HTTP GET request to revoke current token
    facebook_id = login_session['facebook_id']
    url = 'https://accounts.google.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[0]

    if result['status'] == 200:
        # Reset the user's session
        del login_session['facebook_id']
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return jsonify(message='User successfully disconnected from FB.'), 200
    else:
        return jsonify(message='Failed to revoke token for given user.'), 400


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.", "message")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You were not logged in", "message")
        return redirect(url_for('showRestaurants'))


@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurant=[i.serialize for i in restaurants])


# @app.route('/restaurants/RSS/')
# def restaurantsRSS():
#     restaurants = session.query(Restaurant).all()
#     d = feedparser.parse(restaurants)
#     print d.feed.title


@app.route('/restaurants/xml/')
def restaurantsXml():
    """Return Xml format of restaurants list"""
    restaurants = session.query(Restaurant).all()
    top = Element('top')
    for r in restaurants:
        child = SubElement(top, 'child')
        child.text = r.name + r.description
    return prettify(top)
    # return app.response_class(ET.dump(top), mimetype='application/xml')


@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    try:
        restaurants = session.query(Restaurant).all()
        if login_session.get('user_id') is None:
            return render_template(
                'restaurantsPublic.html',
                restaurants=restaurants)
        else:
            owner = getUserInfo(createUser(login_session))
            return render_template(
                'restaurants.html',
                restaurants=restaurants, user=owner)
    except IOError as err:
        # return redirect(url_for(page_not_found(err))
            return 'restaurants not created', 404
    # finally:
    #     flash("This page will show all my restaurants", "message")


# @app.errorhandler(404)   # //todo:error msg: got invalid syntax.
# def page_not_found(e):
#     return render_template('404.html'), 404


# A decorator is a function that returns a function.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if login_session.get('username') is None :
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/restaurants/new/', methods=['POST', 'GET'])
@login_required
def restaurantNew():
    if request.method == 'POST':
        myNewRestaurant = Restaurant(
                                name=request.form['newName'],
                                description=request.form['newDescription'],
                                user_id=login_session.get('user_id'))
        session.add(myNewRestaurant)
        session.commit()
        flash('New restaurant ' + myNewRestaurant.name+' has been created!',
              'message')
        return redirect(url_for('showRestaurants'))
    else:
        owner = createUser(login_session)
        return render_template('newRestaurant.html', user=owner)


@app.route('/restaurants/<int:restaurant_id>/edit/', methods=['POST', 'GET'])
@login_required
def restaurantEdit(restaurant_id):
    rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        rest.name = request.form['newName']
        rest.description = request.form['newDescription']
        session.add(rest)
        session.commit()
        flash('The restaurant ' + rest.name + ' has been edited!',
              'message')
        return redirect(url_for('showRestaurants'))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        return render_template('editRestaurant.html',
                               restaurant_id=restaurant_id, restaurant=rest)


@app.route('/restaurants/<int:restaurant_id>/delete/', methods=['POST', 'GET'])
@login_required
def restaurantDelete(restaurant_id):
    laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if login_session['user_id'] != laRestaurant.user_id:
        return render_template('notAuthorized.html'), 401
    if request.method == 'POST':
        if(laRestaurant):
            session.delete(laRestaurant)
            session.commit()
            flash('Restaurant ' + laRestaurant.name +
                  ' has been sadly deleted...', 'message')
            return redirect(url_for('showRestaurants'))
        else:
            return "no such restaurant found", 404
    else:
        return render_template(
            'deleteRestaurant.html', restaurant_id=restaurant_id,
            restaurant=laRestaurant)


@app.route('/restaurants/<int:restaurant_id>/menu/JSON/')
def restaurantMenuJSON(restaurant_id):
    menus = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    return jsonify(menuItem=[i.serialize for i in menus])


@app.route('/menus/JSON/')
def allMenusJSON():
    menus = session.query(MenuItem).order_by(MenuItem.id)
    return jsonify(menuItem=[i.serialize for i in menus])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON/')
def menuJSON(restaurant_id, menu_id):
    menu = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(menuItem=menu.serialize)


# route() decorator to tell Flask what URL should trigger method
# next line:if w/o default,do as so: showMenus(restaurant_id=1):
# @app.route('/', defaults={'restaurant_id': 1})
# @app.route('/restaurants/<int:restaurant_id>/')
@app.route('/restaurants/<int:restaurant_id>/menu/')
def showMenus(restaurant_id):
    try:
        # without one():'AttributeError: 'Query' object has no attribute 'id''
        rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
        myMenus = session.query(MenuItem).filter_by(
            restaurant_id=restaurant_id).all()
        logged_id = login_session.get('user_id')
        owner_id = rest.user_id
        if logged_id is None or owner_id != logged_id:
            return render_template(
                'menuPublic.html', restaurant=rest,
                restaurant_id=restaurant_id,
                menus=myMenus)
        else:
            return render_template('menu.html', restaurant_id=restaurant_id,
                                   restaurant=rest, menus=myMenus)
    except IOError as err:
        return "No menus available yet.", 404


# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET', 'POST'])
@login_required
def newMenu(restaurant_id):
    rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        myNewMenu = MenuItem(
            name=request.form['newName'],
            course=request.form['newCourse'],
            description=request.form['newDescription'],
            price=request.form['newPrice'],
            restaurant_id=restaurant_id)
        myNewCondition = Condition(name=request.form['newConditions'])
        session.add(myNewCondition)
        myNewMenu.conditions.append(myNewCondition)
        session.add(myNewMenu)
        session.commit()
        flash('New menu ' + myNewMenu.name + ' has been created!', 'message')
        return redirect(url_for('showMenus', restaurant_id=restaurant_id))
    else:
        if login_session.get('user_id') != rest.user_id:
            return redirect(url_for('showLogin'))
        return render_template('newMenuItem.html', restaurant_id=restaurant_id,
                               restaurant=rest)


@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def editMenu(restaurant_id, menu_id):
    rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
    laMenu = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        laMenu.name = request.form['newName']
        laMenu.course = request.form['newCourse']
        laMenu.description = request.form['newDescription']
        laMenu.price = request.form['newPrice']
        session.add(laMenu)
        session.commit()
        flash('The menu ' + laMenu.name + ' has been edited!', 'message')
        return redirect(url_for('showMenus', restaurant_id=restaurant_id))
    else:
        if login_session.get('user_id') != rest.user_id:
            return redirect(url_for('showLogin'))
        return render_template(
            'editMenuItem.html', restaurant_id=restaurant_id,
            menu_id=menu_id, restaurant=rest, menu=laMenu)


# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def deleteMenu(restaurant_id, menu_id):
    rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
    laMenu = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if login_session.get('user_id') != rest.user_id:
            flash('the restaurant ' + rest.name + ' is not created by you', 'message')
            return redirect(url_for('showMenus',restaurant_id=restaurant_id))
        name = laMenu.name
        session.delete(laMenu)
        session.commit()
        flash('the menu ' + name + ' has been deleted!', 'message')
        return redirect(url_for('showMenus', restaurant_id=restaurant_id))
    else:
        if login_session.get('user_id') != rest.user_id:
            return redirect(url_for('showLogin'))
        return render_template(
            'deleteMenuItem.html', restaurant_id=restaurant_id,
            menu_id=menu_id, menu=laMenu)


@app.route('/conditions/')
def showConditions():
    try:
        conditions = session.query(Condition).all()
        if login_session.get('user_id') is None:
            return render_template('conditionsPublic.html',
                                   conditions=conditions)
        else:
            owner = getUserInfo(createUser(login_session))
            return render_template('conditions.html', conditions=conditions,
                                   user=owner)

    except IOError as err:
        return "No conditions, error:"
    # finally:
    #     flash("This page shows all conditions...", "message")


@app.route('/conditions/new/', methods=['POST', 'GET'])
@login_required
def newCondition():
    if request.method == 'POST':
        condition = Condition(
            name=request.form['name'],
            signs_and_symptoms=request.form['signs_and_symptoms'],
            user_id=login_session.get('user_id'))
        session.add(condition)
        session.commit()
        flash('the condition '+condition.name+' has been listed!', 'message')
        return redirect(url_for('showConditions'))
    else:
        return render_template('newCondition.html')


@app.route('/conditions/<int:condition_id>/edit', methods=['POST', 'GET'])
@login_required
def conditionEdit(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    if request.method == 'POST':
        laCondition.name = request.form['newName']
        laCondition.signs_and_symptoms = request.form['newSignsAndSymptoms']
        session.add(laCondition)
        session.commit()
        flash('the condition '+laCondition.name+' has been edited!', 'message')
        return redirect(url_for('showConditions'))
    else:
        if login_session.get('user_id') != laCondition.user_id:
            return redirect(url_for('showLogin'))
        return render_template('editCondition.html', condition_id=condition_id,
                               condition=laCondition)


@app.route('/conditions/<int:condition_id>/delete', methods=['POST', 'GET'])
@login_required
def conditionDelete(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    if request.method == 'POST':
        session.delete(laCondition)
        flash('the condition ' + laCondition.name +
              ' has been deleted!', 'message')
        return redirect(url_for('showConditions'))
    else:
        if login_session.get('user_id') != laCondition.user_id:
            return redirect(url_for('showLogin'))
        return render_template(
            'deleteCondition.html',
            condition_id=condition_id, condition=laCondition)


@app.route('/conditions/<int:condition_id>/menu/')
def conditionMenus(condition_id):
    try:
        laCondition = session.query(Condition).filter_by(id=condition_id).one()
        menus = laCondition.suggested_menus
        logged_id = login_session.get('user_id')
        owner_id = laCondition.user_id
        if logged_id is None or owner_id != logged_id:
            return render_template(
                'conditionMenusPublic.html', condition_id=condition_id,
                condition=laCondition, menus=menus)
        else:
            return render_template(
                'conditionMenus.html', condition_id=condition_id,
                condition=laCondition, menus=menus)
    except IOError as err:
        return "No menus available yet.", 404

#  adds a menu suitable for certain condition to a restaurant
@app.route('/conditions/<int:condition_id>/new/', methods=['GET', 'POST'])
@login_required
def newConditionMenu(condition_id):
    condition = session.query(Condition).filter_by(id=condition_id).one()
    if request.method == 'POST':
        # laRestaurant_id = session.query(Restaurant).filter_by(name=request.form['newRestaurantName']).one().id
        newConditionMenu = MenuItem(
            name=request.form['newName'],
            course=request.form['newCourse'],
            description=request.form['newDescription'],
            price=request.form['newPrice'],
            restaurant_id=request.form['newRestaurantId'])
        newConditionMenu.conditions.append(condition)
        session.add(newConditionMenu)
        session.commit()
        flash('New menu ' + newConditionMenu.name+' has been created!',
              'message')
        return redirect(url_for('conditionMenus', condition_id=condition_id))
    else:
        if login_session.get('user_id') != condition.user_id:
            return redirect(url_for('showLogin'))
        restaurants = session.query(Restaurant).all()
        return render_template(
            'newConditionMenu.html',
            condition_id=condition_id, condition=condition,
            restaurants=restaurants)


if __name__ == '__main__':
    # TODO: set to False before deployment: enable debug so the server
    # reloads itself on code changes
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
