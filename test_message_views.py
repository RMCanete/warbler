"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:2118@localhost/warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 1111
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        r = super().tearDown()
        db.session.rollback()
        return r

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99999
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_delete_message(self):
        message = Message(
            id = 1111,
            test = "message 1",
            user_id = self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post("/messages/1111/delete", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(1111)
            self.assertIsNone(message)

    def test_delete_message_not_logged_in(self):
        message = Message(
            id = 2222,
            test = "message 2",
            user_id = self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/2222/delete", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(2222)
            self.assertIsNotNone(message)

    def test_delete_message_invalid(self):

        user2 = User.signup(
            username = "user2",
            email = "user2@email.com",
            password = "password",
            image_url = None
        )
        user2.id = 2222

        message = Message(
            id = 3333,
            test = "message 3",
            user_id = self.testuser_id
        )
        db.session.add(message)
        db.session.add(user2)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2222
            resp = c.post("/messages/3/delete", follow_redirects = True)
            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(3333)
            self.assertIsNotNone(message)