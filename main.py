from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Manage session info
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine("sqlite:///catalog_with_auth.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()

# Flask App
app = Flask(__name__)

# Endpoints
@app.route('/')
@app.route('/category/')
def categoryList():
    categories = session.query(Category).all()
    return render_template('index.html', categories=categories, user=login_session.get('username'))

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase +
        string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, user=login_session.get('username'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode("utf-8"))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
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
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    print(data)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    u_id = getUserId(login_session['email'])
    if u_id:
        login_session['user_id'] = u_id
    else:
        login_session['user_id'] = createUser(login_session)

    output = '<div class="text-center">'
    output += '<h3>Welcome, '
    output += login_session['username']
    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> </div>'
    flash ("You are now logged in as {}".format(login_session['username']))
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print ('result is ')
    print (result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully logged out.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response
        flash ("Successfully Logged out.")
        return redirect(url_for('categoryList'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/category/<int:category_id>/')
def categoryItems(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category=category)
    items_list = []
    if login_session.get('email'):
        for i in items:
            if i.user_id == getUserId(login_session['email']):
                items_list.append({"item": i, "auth": True})
            else:
                items_list.append({"item": i, "auth": False})
    else:
        for i in items:
            items_list.append({"item": i, "auth": False})
    return render_template('items.html', category=category, items=items, items_list=items_list,
        user=login_session.get('username'))


@app.route('/category/<int:category_id>/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
            description=request.form['description'],
            category_id=category_id,
            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("New item created!")
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('new_item.html', category=category,
            user=login_session.get('username'))


@app.route('/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    
    item = session.query(Item).filter_by(id=item_id).one()
    
    if login_session['user_id'] != item.user_id:
        flash("Access Denied")
        return redirect(url_for('categoryItems', category_id=category_id))
    
    if request.method =='POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = request.form['category']
        session.add(item)
        session.commit()
        flash("Item has been updated!")
        return redirect(url_for('categoryItems', category_id=item.category_id))
    else:
        categories = session.query(Category).all()
        return render_template("edit_item.html", categories=categories, category_id=category_id,
            item=item, user=login_session.get('username'))


@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(Item).filter_by(id=item_id).one()

    # Check whether user is authorized to delete an item (Stop direct access)
    if login_session['user_id'] != item.user_id:
        flash("Access Denied")
        return redirect(url_for('categoryItems', category_id=category_id))

    if request.method == 'POST':
        item = session.query(Item).filter_by(id=item_id).one()

        # Check for deletion via POST 
        if item.user_id != login_session['user_id']:
            flash("Access Denied")
            return redirect(url_for('categoryItems', category_id=category_id))
        session.delete(item)
        session.commit()
        flash("Item deleted!")
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template('delete_item.html', category_id=category_id,
            item=item)


# API endpoints
@app.route('/category/<int:category_id>.json')
def categoryItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category=category).all()
    return jsonify(items=[i.serialize for i in items])

@app.route('/item/<int:item_id>.json')
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item.serialize)


# Helper functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
        email = login_session['email'],
        picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
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

# Main
if __name__ == "__main__":
    app.secret_key = 'some_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)