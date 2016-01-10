from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
# import manyRestaurants
app = Flask(__name__)
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, MenuItem, Condition, Base, User, engine

# New imports for state token
from flask import session as login_session
import random
import string

# import for new gconnect using verify_id_token API
from oauth2client import client, crypt

# IMPORTS FOR gconnect
from oauth2client.client import flow_from_clientsecrets  # creates a Flow object from a client_secrets.json file
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests # Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.

# from Facebook OAuth 2 Tutorial
# from requests_oauthlib import OAuth2Session
# from requests_oauthlib.compliance_fixes import facebook_compliance_fix

# if just do 'from manyRestaurants import Restaurant, session' and without the next 4 lines,get error
# 'SQLite objects created in a thread can only be used in that same thread'
engine = create_engine('sqlite:///restaurantmenuconditionuser.db',echo=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

G_CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "Therapeutic Foods Restaurants"

# Here I added id init, different from instructor's; removed; unique constraint
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture']
                   )
    session.add(newUser)
    session.commit()
    # user=session.query(User).filter_by(email=login_session['email']).one() # TODO: multiple rows were found for one()
    user=session.query(User).filter_by(email=login_session['email']).first()
    print user.name
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


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
        return jsonify(message='Invalid state parameter.'),401
    # Obtain the one-time authorization code from authorization server
    code = request.data
    print 'code'
    print code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='', # creates a Flow object from a client_secrets.json file
                                             redirect_uri = 'postmessage')
        credentials = oauth_flow.step2_exchange(code)  # exchanges an authorization code for a Credentials object
    except FlowExchangeError:
        return jsonify(message='Failed to upgrade the authorization code.'), 401

    # Check that the access token is valid.
    # A Credentials object holds refresh and access tokens that authorize access
    # to a single user's data. These objects are applied to httplib2.Http objects to
    # authorize access.
    print credentials
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1]) # loads:Deserialize to a Python object
    print "result:",result
    # If there was an error in the access token info, abort.
    # dict.get(key, default=None)
    # The method get() returns a value for the given key. If key unavailable then returns default None.
    if result.get('error') is not None:
        # response = make_response(json.dumps(result.get('error')), 500)
        # response.headers['Content-Type'] = 'application/json'
        return jsonify(message=result.get('error')),500



    # Verify that the access token is used for the intended user.
    # id_token: object, The identity of the resource owner.
    # 'Google ID Token's field (or claim) 'sub' is unique-identifier key for the user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps
            ("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        return jsonify(message="Token's user ID doesn't match given user ID."),401

    # Verify that the access token is valid for this app.
    if result['issued_to'] != G_CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
        return jsonify(message="Token's client ID does not match app's."),401


    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        # response = make_response(json.dumps('Current user is already connected.'),
        #                          200)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return jsonify(message='Current user is already connected.'),200

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = credentials.access_token

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check to see if user exist
    # user = session.query(User).one()
    # if user is None:
    #     createUser(login_session)
    # print user.name
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done gconnect!"
    return output



@app.route('/gdisconnect/')
def gdisconnect():  # TODO: put on login.html?
    # Only a connected user
    print 'login_session:',login_session
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
        # return jsonify(message='Why, current user not connected.'),401

    # Execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    print 'access_token:',access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')
    print 'gdisconnect request result:', result
    print "login_session['username'] before del:",login_session['username']
    if result[0]['status'] == 200:  # TODO: why 200 means to clear cache while '200' not
        # Reset the user's session
        del login_session['credentials']
        del login_session['gplus_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        del login_session['user_id']
        print "login_session['username'] after del:",login_session['username']
        # response = make_response(json.dumps('User successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return  response
        return jsonify(message='User successfully disconnected.'), 200
    else:
        # response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        # response.headers['Content-Type'] = 'application/json'
        # return response
        return jsonify(message='Failed to revoke token for given user.'), 400


@app.route('/fbconnect/', methods=['POST'])
def fbconnect():
    # Validate state token
    print request.args.get('state')
    print login_session['state']
    if request.args.get('state') != login_session['state']: # check what client sent is what server sent
        response = make_response(json.dumps('Invalid state parameter.'), 401)  #dumps:Serialize obj to a JSON formatted str
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain the one-time authorization code from authorization server
    code = request.data
    print 'code'
    print code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('fb_client_secrets.json', scope='', # creates a Flow object from a client_secrets.json file
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
    print 'credentials'
    print credentials
    access_token = credentials.access_token
    app_info = json.loads(open('fb_client_secret.json','r').read())
    print app_info.json() # why print not working?
    app_id = app_info['web']['app_id']
    app_secret = app_info['web']['app_secret']
    token_url = 'https://graph.facebook.com/oauth/access_token?\
                 grant_type=fb_exchange_token&\
                 client_id=%s&\
                 client_secret=%s&\
                 fb_exchange_token=%s' % (app_id,app_secret,access_token)

    # redirect_uri = 'http://localhost:5000/'
    # facebook = OAuth2Session(client_id, redirect_uri=redirect_uri)
    # facebook = facebook_compliance_fix(facebook)
    # access_token = facebook.fetch_token(token_url, client_secret=client_secret)
    # print 'Please go here and authorize,', authorization_url


    h = httplib2.Http()
    # result = json.loads(h.request(token_url, 'GET')[1]) # loads:Deserialize to a Python object

    result = h.request(token_url, 'GET')[1]
    token = result.split("&")[0]
    print result[0]

    userinfo_url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    data=json.loads(h.request(userinfo_url, 'GET'))


    # stored_credentials = login_session.get('credentials')
    # stored_gplus_id = login_session.get('gplus_id')
    # if stored_credentials is not None and gplus_id == stored_gplus_id:
    #     response = make_response(json.dumps('Current user is already connected.'),
    #                              200)
    #     response.headers['Content-Type'] = 'application/json'
    #     return response

    # Store the access token in the session for later use.

    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    user_pic_url = 'https://graph.facebook.com/v2.5/me/picture?%s \
                    &redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    pic = json.loads(h.request(user_pic_url, 'GET'))
    login_session['picture'] = pic['data']['url']

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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done via FB!"
    return output

@app.route('/fbdisconnect/')
def fbdisconnect():  # TODO: put on login.html?

    # Execute HTTP GET request to revoke current token
    facebook_id = login_session['facebook_id']
    url = 'https://accounts.google.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[0] # TODO

    if result['status'] == 200:  # TODO: why 200 means to clear cache while '200' not
        # Reset the user's session
        del login_session['facebook_id']
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        # response = make_response(json.dumps('User successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        # return  response
        return jsonify(message='User successfully disconnected from FB.'), 200
    else:
        # response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        # response.headers['Content-Type'] = 'application/json'
        # return response
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
        flash("You have successfully been logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showRestaurants'))

# @app.route('/disconnect/')
# def disconnect():
#     if 'provider' in login_session:
#         if login_session['provider'] == 'google':
#             gdisconnect()
#             return redirect(url_for('gdisconnect'))
#         elif login_session['provider'] == 'facebook':
#             return redirect(url_for('fbdisconnect'))
#     else:
#         flash('You are not logged in to begin with!')
#         return redirect(url_for('showRestaurants'))

@app.route('/restaurants/JSON/')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurant=[i.serialize for i in restaurants])

@app.route('/restaurants/')
def showRestaurants():
    try:
        restaurants = session.query(Restaurant).all()
        # if login_session['user_id'] == owner_id : TODO: why this line cause [KeyError: 'user_id']
        if login_session.get('user_id') is None:
            return render_template('restaurantsPublic.html', restaurants=restaurants)
        else:
            owner = getUserInfo(createUser(login_session)) #aha! This addressed 'username' error
            return render_template('restaurants.html', restaurants=restaurants,user=owner)
    except IOError as err:
        return "No restaurant, error:"
    finally:
        flash("This page will show all my restaurants")

@app.route('/restaurants/new/', methods=['POST','GET'])
def restaurantNew():
    if request.method == 'POST':
        myNewRestaurant = Restaurant(name=request.form['newName'],
                                     description=request.form['newDescription'],
                                     user_id=login_session['user_id'])
        session.add(myNewRestaurant)
        session.commit()
        flash('New restaurant ' + myNewRestaurant.name+' has been created!')
        return redirect(url_for('showRestaurants'))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        else:
            owner = createUser(login_session['user_id'])
            return render_template('newRestaurant.html',user=owner)

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
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        return render_template('editRestaurant.html', restaurant_id=restaurant_id,restaurant=laRestaurant)

@app.route('/restaurants/<int:restaurant_id>/delete/',methods=['POST','GET'])
def restaurantDelete(restaurant_id):
    laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if login_session.get('username') is None:
        return redirect(url_for('showLogin'))
    if login_session['user_id'] != laRestaurant.user_id:
        return render_template('notAuthorized.html')
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

@app.route('/menus/JSON/')
def allMenusJSON():
    menus = session.query(MenuItem).order_by(MenuItem.id)
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
    myMenus = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    owner = getUserInfo(laRestaurant.user_id)
    if login_session.get('username') is None or laRestaurant.user_id != login_session['user_id']:
        return render_template('menuPublic.html', restaurant=laRestaurant, menus=myMenus)
    else:
        return render_template('menu.html', restaurant=laRestaurant, menus=myMenus,user=owner)

# @app.route('/')
@app.route('/restaurants/<int:restaurant_id>/new/', methods=['GET','POST'])
def newMenu(restaurant_id):
    if request.method == 'POST':
        laRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        myNewMenu = MenuItem(name=request.form['newName'],
                             course=request.form['newCourse'],
                             description=request.form['newDescription'],
                             price=request.form['newPrice'],
                             restaurant_id=restaurant_id,
                             user_id=laRestaurant.user_id)
        session.add(myNewMenu)
        session.commit()
        flash('New menu ' + myNewMenu.name+' has been created!')
        return redirect(url_for('showMenus',restaurant_id=restaurant_id))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
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
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
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
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        return render_template('deleteMenuItem.html', restaurant_id=restaurant_id, menu_id=menu_id, menu=laMenu)

@app.route('/conditions/')
def showConditions():
    try:
        conditions = session.query(Condition).all()
        return render_template('conditions.html', conditions=conditions)
    except IOError as err:
        return "No conditions, error:"
    finally:
        flash("This page will show all conditions")

@app.route('/conditions/new/', methods=['POST','GET'])
def newCondition():
    if request.method == 'POST':
        condition = Condition(name=request.form['name'],
                              signs_and_symptoms=request.form['signs_and_symptoms'],
                              user_id=login_session['user_id']
                              )
        session.add(condition)
        session.commit()
        flash('the condition '+condition.name+' has been listed!')
        return redirect(url_for('showConditions'))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        return render_template('newCondition.html')


@app.route('/conditions/<int:condition_id>/edit', methods=['POST','GET'])
def conditionEdit(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    if request.method == 'POST':
        laCondition.name = request.form['newName']
        laCondition.signs_and_symptoms = request.form['newSignsAndSymptoms']
        session.add(laCondition)
        session.commit()
        flash('the condition '+laCondition.name+' has been edited!')
        return redirect(url_for('showConditions'))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        return render_template('editCondition.html',condition_id=condition_id,condition=laCondition)

@app.route('/conditions/<int:condition_id>/delete',methods=['POST','GET'])
def conditionDelete(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    if request.method == 'POST':
        session.delete(laCondition)
        flash('the condition '+laCondition.name+' has been deleted!')
        return redirect(url_for('showConditions'))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        return render_template('deleteCondition.html',condition_id=condition_id,condition=laCondition)

@app.route('/conditions/<int:condition_id>/menu/')
def conditionMenus(condition_id):
    laCondition = session.query(Condition).filter_by(id=condition_id).one()
    menus = laCondition.suggested_menus
    return render_template('conditionMenus.html', condition_id=condition_id,condition=laCondition, menus=menus)

# this method allows to add a menu suitable for certain condition to a restaurant
@app.route('/conditions/<int:condition_id>/new/', methods=['GET','POST'])
def newConditionMenu(condition_id):
    if request.method == 'POST':
        laCondition = session.query(Condition).filter_by(id=condition_id).one()
        laRestaurant_id = session.query(Restaurant).filter_by(name=request.form['newRestaurantName']).one().id
        newConditionMenu = MenuItem(name=request.form['newName'],
                             course=request.form['newCourse'],
                             description=request.form['newDescription'],
                             price=request.form['newPrice'],
                             restaurant_id=request.form['newRestaurantId'],
                             user_id=login_session['user_id'])
        newConditionMenu.conditions.append(laCondition)
        # laCondition.suggested_menus.append(newConditionMenu)
        session.add(newConditionMenu)
        # session.add(laCondition)
        session.commit()
        flash('New menu ' + newConditionMenu.name+' has been created!')
        return redirect(url_for('conditionMenus',condition_id=condition_id))
    else:
        if login_session.get('username') is None:
            return redirect(url_for('showLogin'))
        laCondition = session.query(Condition).filter_by(id=condition_id).one()
        restaurants = session.query(Restaurant).all()
        return render_template('newConditionMenu.html',condition_id=condition_id, condition=laCondition,restaurants=restaurants)

if __name__ == '__main__':
    # If you enable debug support the server will reload itself on code changes
    app.secret_key='super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
