from flask import Flask
# import manyRestaurants
app = Flask(__name__)

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
@app.route('/hello')
def HelloWorld():

    laRestaurant = session.query(Restaurant).first()
    myMenus = session.query(MenuItem).filter_by(restaurant_id=laRestaurant.id).all()
    output=''
    for menu in myMenus:
        output += menu.course
        output += '</br>'
        output += menu.name
        output += '</br>'
        output += menu.description
        output += '</br>'
        output += menu.price
        output += '</br>'

    return output

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)