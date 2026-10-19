from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="member")
    issues = db.relationship("Issue", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    issues = db.relationship("Issue", back_populates="book")


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=utc_now)
    return_date = db.Column(db.DateTime)
    fine_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    user = db.relationship("User", back_populates="issues")
    book = db.relationship("Book", back_populates="issues")
    fine = db.relationship("Fine", back_populates="issue", uselist=False)


class Fine(db.Model):
    __tablename__ = "fines"

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(
        db.Integer, db.ForeignKey("issues.id"), nullable=False, unique=True
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.Boolean, nullable=False, default=False)
    issue = db.relationship("Issue", back_populates="fine")


class Search(db.Model):
    __tablename__ = "searches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    query = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utc_now)
    results = db.Column(db.JSON)
    user = db.relationship("User")
