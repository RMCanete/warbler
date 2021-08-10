"""User model tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
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

        user2 = User.signup("user2", "user2@email.com", "password", None)
        user2id = 2222
        user2.id = user2id

        db.session.commit()

        user1 = User.query.get(user1id)
        self.user1 = user1
        self.user1id = user1id

        user2 = User.query.get(user2id)  
        self.user2 = user2
        self.user2id = user2id

        self.client = app.test_client()

    def tearDown(self):
        r = super().tearDown()
        db.session.rollback()
        return r

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_valid_signup(self):
        user = User.signup("userTest", "userTest@email.com", "password", None)
        user_id = 3333
        user.id = user_id
        db.session.commit()

        user = User.query.get(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "userTest")
        self.assertEqual(user.email, "userTest@email.com")
        self.assertNotEqual(user.password, "password")
        self.assertTrue(user.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalidUser = User.signup(None, "invalidUser@email.com", "password", None)
        user_id = 4444
        invalidUser.id = user_id
        with self.assertRaises(exc.IntegrityError) as text:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as text:
            User.signup("user", "user@gmail.com", None, None)

    def test_invalid_email_signup(self):
        invalidUser1 = User.signup(None, None, "password", None)
        user_id = 5555
        invalidUser1.id = user_id
        with self.assertRaises(exc.IntegrityError) as text:
            db.session.commit()
    
    def test_valid_authentication(self):
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("nonexistantusername", "password"))
    
    def test_invalid_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "incorrectpassword"))

