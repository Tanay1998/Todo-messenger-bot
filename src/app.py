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
        print 'User %d, username %s' % (user.id, user.username)
        for todo in user.todos:
            print 'Todo %d: %s at' % (todo.id, todo.text)

    # Render all of this into an HTML template and return it. We use
    # User.query.all() to obtain a list of all users, rather than an
    # iterator. This isn't strictly necessary, but just to illustrate that both
    # User.query and User.query.all() are both possible options to iterate over
    # query results.
    return flask.render_template('index.html', users=User.query.all())


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
            curUser = User.query.filter_by(sender_id=sender_id)
            if curUser == None:
                curUser = User(sender_id=sender_id)
                db.session.add(curUser)
                db.session.commit()


            message_text = (message['text']).lower().strip()
            print "Got: " + message_text
            
            # Process message_text & Get message to send 
            if message_text == "list":
                message_send = "Print list"

            elif message_text == "list done":
                message_send = "Print finished list"

            else:
                query = message_text.split()
                if query[0] == "add":
                    text = query[1:].join(' ')
                    message_send = "Adding " + text

                elif query[0][0] == '#':
                    index = int(query[0][1:])
                    if query[1] == "done":
                        message_send = "Finished " + str(index)

                    elif query[1] == "delete":
                        message_send = "Deleting " + str(index)


            request_url = FACEBOOK_API_MESSAGE_SEND_URL % (app.config['FACEBOOK_PAGE_ACCESS_TOKEN'])
            requests.post(request_url, headers={'Content-Type': 'application/json'},
                          json={'recipient': {'id': sender_id}, 'message': {'text': message_send}})

    # Return an empty response.
    return ''

if __name__ == '__main__':
    app.run(debug=True)
