"""
Flask Documentation:     http://flask.pocoo.org/docs/
Flask-SQLAlchemy Documentation: http://flask-sqlalchemy.pocoo.org/
SQLAlchemy Documentation: http://docs.sqlalchemy.org/
FB Messenger Platform docs: https://developers.facebook.com/docs/messenger-platform.

This file creates your application.
"""

import os
import flask
import requests
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

FACEBOOK_API_MESSAGE_SEND_URL = (
    'https://graph.facebook.com/v2.6/me/messages?access_token=%s')

app = flask.Flask(__name__)

# TODO: Set environment variables appropriately.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['FACEBOOK_PAGE_ACCESS_TOKEN'] = os.environ[
    'FACEBOOK_PAGE_ACCESS_TOKEN']
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mysecretkey')
app.config['FACEBOOK_WEBHOOK_VERIFY_TOKEN'] = 'mysecretverifytoken'


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(80), unique=True)


class TodoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    text = db.Column(db.String, nullable=False)
    dateAdded = db.Column(db.Date, nullable=False)
    dateCompleted = db.Column(db.Date, nullable=True) #None if event not completed

    # Connect each address to exactly one user.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # This adds an attribute 'user' to each address, and an attribute
    # 'addresses' (containing a list of addresses) to each user.
    user = db.relationship('User', backref='todos')


@app.route('/')
def index():
    """Simple example handler.

    This is just an example handler that demonstrates the basics of SQLAlchemy,
    relationships, and template rendering in Flask.

    """
    # Just for demonstration purposes
    for user in User.query:  #
        print 'User %d, username %s' % (user.id, user.sender_id)
        for todo in user.todos:
            print 'Todo %d: %s at' % (todo.id, todo.text)

    # Render all of this into an HTML template and return it. We use
    # User.query.all() to obtain a list of all users, rather than an
    # iterator. This isn't strictly necessary, but just to illustrate that both
    # User.query and User.query.all() are both possible options to iterate over
    # query results.
    return flask.render_template('index.html', users=User.query.all())

def get_todo_tasks(user, isComplete = False):
    if isComplete:
        return TodoItem.query.filter_by(user=user).filter(TodoItem.dateCompleted != None).order_by(TodoItem.dateAdded).all()
    else:
        return TodoItem.query.filter_by(user=user).filter_by(dateCompleted=None).order_by(TodoItem.dateAdded).all()

def word_has(word, matches):
    for match in matches: 
        if match in word.lower():
            return True
    return False

@app.route('/fb_webhook', methods=['GET', 'POST'])
def fb_webhook():
    """This handler deals with incoming Facebook Messages.

    In this example implementation, we handle the initial handshake mechanism,
    then just echo all incoming messages back to the sender. Not exactly Skynet
    level AI, but we had to keep it short...

    """
    # Handle the initial handshake request.
    if flask.request.method == 'GET':
        if (flask.request.args.get('hub.mode') == 'subscribe' and
            flask.request.args.get('hub.verify_token') ==
            app.config['FACEBOOK_WEBHOOK_VERIFY_TOKEN']):
            challenge = flask.request.args.get('hub.challenge')
            return challenge
        else:
            print 'Received invalid GET request'
            return ''  # Still return a 200, otherwise FB gets upset.

    # Get the request body as a dict, parsed from JSON.
    payload = flask.request.json

    # TODO: Validate app ID and other parts of the payload to make sure we're
    # not accidentally processing data that wasn't intended for us.

    # Handle an incoming message.
    # TODO: Improve error handling in case of unexpected payloads.
    for entry in payload['entry']:
        for event in entry['messaging']:
            if 'message' not in event:
                continue
            message = event['message']
            # Ignore messages sent by us.
            if message.get('is_echo', False):
                continue
            # Ignore messages with non-text content.
            if 'text' not in message:
                continue
            sender_id = event['sender']['id']

            #Get user 
            curUser = User.query.filter_by(sender_id=sender_id).first()
            if curUser == None:
                curUser = User(sender_id=sender_id)
                db.session.add(curUser)
                db.session.commit()

            message_text = (message['text']).strip()
            print "Got: " + message_text

            '''
                Process message_text & Get message to send 
            '''

            message_send = "Invalid command."

            # To view list of completed tasks
            if word_has(message_text, ["list"]) and word_has(message_text, ["done", "complete"]):       
                message_send = "Completed Tasks:"

                completeTodos = get_todo_tasks(curUser, True)
                for i in range(len(completeTodos)):
                    todo = completeTodos[i]
                    message_send += "\n#%d: %s" % (i + 1, todo.text)
                if len(completeTodos) == 0:
                    message_send = "No tasks completed yet!"

            elif word_has(message_text, ["list"]):              #To view list of tasks todo
                message_send = "Tasks Todo:"
                incompleteTodos = get_todo_tasks(curUser, False)
                for i in range(len(incompleteTodos)):
                    todo = incompleteTodos[i]
                    message_send += "\n#%d: %s" % (i + 1, todo.text)
                if len(incompleteTodos) == 0:
                    message_send = "No tasks todo!"            

            elif word_has(message_text, ["clear", "delete", "remove", "erase"]) and word_has(message_text, ["all"]):
                deleteIncomplete = False 
                deleteComplete = False 
                if word_has(message_text, [" complete", " finish"]):
                    deleteComplete = True
                if word_has(message_text, [" incomplete", " todo"]):
                    deleteIncomplete = True
                if not deleteIncomplete and not deleteComplete:
                    deleteIncomplete, deleteComplete = True, True

                if deleteComplete:
                    TodoItem.query.filter_by(user=user).filter(TodoItem.dateCompleted != None).delete(synchronize_session=False)
                if deleteIncomplete:
                    TodoItem.query.filter_by(user=user).filter_by(dateCompleted = None).delete(synchronize_session=False)

            elif len(message_text) > 0:
                query = message_text.split()

                if len(query) > 1 and word_has(query[0], ["search"]):
                    searchQuery = ' '.join(query[1:])
                    todoList = TodoItem.query.filter_by(user=curUser).order_by(TodoItem.dateAdded).all()
                    matches = []
                    for i in range(len(todoList)):
                        todo = todoList[i]
                        if searchQuery in todo.text:
                            matches.append(todo.text + (" (Incomplete)" if todo.dateCompleted == None else " (Finished)"))
                    if len(matches) == 0:
                        message_send = "No matches found for search"
                    else:
                        message_send = "Found %d results: " % (len(matches))
                        for match in matches:
                            message_send += "\n" + match

                elif len(query) > 1 and word_has(query[0], ["add", "insert", "input"]):               # For adding a new todo
                    text = ' '.join(query[1:])
                    newTodo = TodoItem(text=text, user=curUser, dateAdded=datetime.utcnow(), dateCompleted=None)
                    db.session.add(newTodo)
                    db.session.commit()
                    message_send = "To-do item '" + text + "' added to list."

                elif len(query) > 1 and query[0][0] == '#':            # For Marking as complete and deleting
                    index = int(query[0][1:])
                    if word_has(query[1], ["finish", "done", "complete"]):
                        todoList = get_todo_tasks(curUser, False)
                        if index > len(todoList):
                            message_send = "A task with this index does not exist"
                        else: 
                            curTodo = todoList[index - 1]
                            curTodo.dateCompleted = datetime.utcnow()
                            db.session.commit()
                            message_send = "Finished " + query[0] + ": " + curTodo.text

                    elif word_has(query[1], ["remove", "delete", "clear", "erase"]):
                        todoList = get_todo_tasks(curUser, False)
                        if index > len(todoList):
                            message_send = "A task with this index does not exist"
                        else: 
                            curTodo = todoList[index - 1]
                            db.session.delete(curTodo)
                            db.session.commit()
                            message_send = "Deleted " + query[0] + ": " + curTodo.text


            request_url = FACEBOOK_API_MESSAGE_SEND_URL % (app.config['FACEBOOK_PAGE_ACCESS_TOKEN'])
            requests.post(request_url, headers={'Content-Type': 'application/json'},
                          json={'recipient': {'id': sender_id}, 'message': {'text': message_send}})

    # Return an empty response.
    return ''

if __name__ == '__main__':
    app.run(debug=True)
