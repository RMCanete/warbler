"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import Follows, db, connect_db, Message, User

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

        self.user2 = User.signup("user2", "user2@email.com", "password", None)
        self.user2_id = 2222
        self.user2.id = self.user2_id
        self.user3 = User.signup("user3", "user3@email.com", "password", None)
        self.user3_id = 3333
        self.user3.id = self.user3_id

        db.session.commit()

    def tearDown(self):
        r = super().tearDown()
        db.session.rollback()
        return r

    def test_user_list(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", set(resp.data))
            self.assertIn("@user2", set(resp.data))
            self.assertIn("@user3", set(resp.data))

    def test_show_user(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))

    def test_show_user_follows(self):
        follow1 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        
        db.session.add(follow1)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(follow1), 1)            

    def test_show_user_following(self):
        follow1 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        
        db.session.add(follow1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.get(f"/users/{self.testuser_id}/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@user2", str(resp.data))
            self.assertNotIn("@user3", str(resp.data))

    def test_show_user_followers(self):
        follow1 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        
        db.session.add(follow1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@user2", str(resp.data))
            self.assertNotIn("@user3", str(resp.data))

    def test_show_prohibited_user_following(self):
        follow1 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        
        db.session.add(follow1)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertNotIn("@user2", str(resp.data))

    def test_show_prohibited_user_followers(self):
        follow1 = Follows(user_being_followed_id = self.user2_id, user_following_id = self.testuser_id)
        
        db.session.add(follow1)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            self.assertNotIn("@user2", str(resp.data))