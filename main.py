from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()
# Database setup ends


app = Flask(__name__)

@app.route('/')
@app.route('/category/')
def categoryList():
    categories = session.query(Category).all()
    return render_template('index.html', categories=categories)


@app.route('/category/<int:category_id>/')
def categoryItems(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category=category)
    return render_template('items.html', category=category, items=items)


@app.route('/category/<int:category_id>/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("New item created!")
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template('new_item.html', category_id=category_id)


@app.route('/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method =='POST':
        item.name = request.form['name']
        item.description = request.form['description']
        session.add(item)
        session.commit()
        flash("Item has been updated!")
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template("edit_item.html", category_id=category_id, item=item)


@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        item = session.query(Item).filter_by(id=item_id).one()
        session.delete(item)
        session.commit()
        flash("Item deleted!")
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template('delete_item.html', category_id=category_id, item=item)
        

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

if __name__ == "__main__":
    app.secret_key = 'some_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)