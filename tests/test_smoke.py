import tempfile
import unittest

from backend import db
from backend.app import create_app
from backend.models import Book, Issue


class LibraryAppSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.temp_dir.name}/test.db",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        self.temp_dir.cleanup()

    def register_and_login(self):
        self.client.post(
            "/register",
            data={"username": "reader", "password": "correct-horse-battery"},
            follow_redirects=True,
        )
        return self.client.post(
            "/login",
            data={"username": "reader", "password": "correct-horse-battery"},
            follow_redirects=True,
        )

    def test_health_and_public_home(self):
        self.assertEqual(self.client.get("/health").json, {"status": "ok"})
        self.assertEqual(self.client.get("/ready").json, {"status": "ready"})
        self.assertEqual(self.client.get("/").status_code, 200)
        static_response = self.client.get("/static/css/style.css")
        self.assertEqual(static_response.status_code, 200)
        static_response.close()

    def test_auth_catalog_checkout_and_return_flow(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)

        self.register_and_login()
        response = self.client.post(
            "/add-book",
            data={"title": "Example Book", "author": "A. Reader", "isbn": "1234567890123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Example Book", response.data)

        with self.app.app_context():
            book = Book.query.filter_by(isbn="1234567890123").one()
            book_id = book.id

        response = self.client.post(
            "/issue-book", data={"book_id": str(book_id)}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            issue = Issue.query.one()
            issue_id = issue.id

        response = self.client.post(
            f"/return-book/{issue_id}", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Issue, issue_id).return_date)


if __name__ == "__main__":
    unittest.main()
