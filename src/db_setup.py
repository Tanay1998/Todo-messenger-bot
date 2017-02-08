from app import TodoItem, User, db

db.drop_all()
db.create_all()

user = User(username='admin')
todo1 = TodoItem(text='Eat cookie', user=admin, date=datetime.utcnow(), dateCompleted=datetime.utcnow())
todo2 = TodoItem(text='Wash clothes', user=admin, date=datetime.utcnow(), dateCompleted=None)

db.session.add(user)  # This will also add admin_address to the session.
db.session.add(todo1)  # This will also add guest_address to the session.
db.session.add(todo2)  # This will also add guest_address to the session.

db.session.commit()

print User.query.all()
print TodoItem.query.all()
