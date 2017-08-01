from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine("sqlite:///catalog_with_auth.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()

print ("Users are:")
for user in session.query(User).all():
    print (user.id)
    print (user.name)
    print (user.email)
    print ('\n')

print ("====================================")

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
    print (item.category.name)
    print (item.user.name)
    print ('\n')