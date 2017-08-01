from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine("sqlite:///catalog_with_auth.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()

# Adding user

mUser = User(name="Chirag Khurana", email="ckhurana000@gmail.com", picture="https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg")
session.add(mUser)
session.commit()


# Adding categories

mCategory1 = Category(name="Python")
mCategory2 = Category(name="JavaScript")
mCategory3 = Category(name="Ruby")

session.add(mCategory1)
session.add(mCategory2)
session.add(mCategory3)

session.commit()


# Adding Items

mItem = Item(name="Flask", category=mCategory1, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="Django", category=mCategory1, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="SQLAlchemy", category=mCategory1, description="Database library", user=mUser)
session.add(mItem)
session.commit()


mItem = Item(name="jQuery", category=mCategory2, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="React", category=mCategory2, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="Angular", category=mCategory2, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="Node.js", category=mCategory2, user=mUser)
session.add(mItem)
session.commit()

mItem = Item(name="Ruby with Rails", category=mCategory3, user=mUser)
session.add(mItem)
session.commit()

# mCategory = session.query(Category).filter_by(name = "JavaScript").one()
# mItem = Item(name="jQuery", category=mCategory)
# session.add(mItem)
# session.commit()


print ("Categories are:")
for category in session.query(Category).all():
    print (category.id)
    print (category.name)
    print ('\n')

print ("====================================")

print ("Items are:")
for item in session.query(Item).all():
    print (item.id)
    print (item.name)
    print ('\n')