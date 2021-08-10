"""Message model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:2118@localhost/warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        db.drop_all()
        db.create_all()

        user1 = User.signup("user1", "user1@email.com", "password", None)
        user1id = 1111
        user1.id = user1id

        db.session.commit()

        self.user1 = User.query.get(self.user1id)

        self.client = app.test_client()

    def tearDown(self):
        r = super().tearDown()
        db.session.rollback()
        return r

    def test_message_model(self):
        """Does basic model work?"""

        user2 = User.signup("user2", "user2@email.com", "password", None)
        user2id = 2222
        user2.id = user2id

        message = Message(
            text = "test",
            user_id = self.user2id
        )

        db.session.add(message)
        db.session.add(user2)
        db.session.commit()

        # User should have one messages
        self.assertEqual(len(user2.messages), 1)

    def test_message_likes(self):

        message1 = Message(
            text = "test1",
            user_id = self.user1id
        )
    
        user3 = User.signup("user3", "user3@email.com", "password", None)
        user3id = 3333
        user3.id = user3id

        db.session.add(message1)
        db.session.add(user3)
        db.session.commit()

        user3.likes.append(message1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == user3id).all()
        self.assertEqual(len(like), 1)