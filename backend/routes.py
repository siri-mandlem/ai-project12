from decimal import Decimal
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend import db
from backend.models import Book, Issue, Search, User, utc_now


main = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


@main.app_context_processor
def inject_current_user():
    user_id = session.get("user_id")
    return {"current_user": db.session.get(User, user_id) if user_id else None}


@main.get("/health")
def health():
    return {"status": "ok"}


@main.get("/ready")
def ready():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Database readiness check failed")
        return {"status": "unavailable"}, 503
    return {"status": "ready"}


@main.get("/base")
@main.get("/base.html")
def base_template():
    return render_template("base.html")


@main.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main.route("/register", methods=["GET", "POST"])
@main.get("/register.html")
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already registered.", "error")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("That username is already registered.", "error")
            else:
                flash("Account created. Please sign in.", "success")
                return redirect(url_for("main.login"))
    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
@main.get("/login.html")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@main.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("main.home"))


@main.get("/dashboard")
@main.get("/dashboard.html")
@login_required
def dashboard():
    user_id = session["user_id"]
    active_issues = Issue.query.filter_by(
        user_id=user_id, return_date=None
    ).order_by(Issue.issue_date.desc()).all()
    available_books = Book.query.filter(
        ~Book.issues.any(Issue.return_date.is_(None))
    ).count()
    return render_template(
        "dashboard.html",
        active_issues=active_issues,
        available_books=available_books,
    )


@main.route("/add-book", methods=["GET", "POST"])
@main.get("/add-book.html")
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip()
        if not title or not author or not isbn:
            flash("Title, author, and ISBN are required.", "error")
        elif len(isbn) > 13:
            flash("ISBN must be no more than 13 characters.", "error")
        elif Book.query.filter_by(isbn=isbn).first():
            flash("A book with that ISBN already exists.", "error")
        else:
            db.session.add(Book(title=title, author=author, isbn=isbn))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("A book with that ISBN already exists.", "error")
            else:
                flash("Book added to the catalog.", "success")
                return redirect(url_for("main.list_books"))
    return render_template("add-book.html")


@main.get("/list-books")
@main.get("/list-books.html")
@main.get("/books")
@login_required
def list_books():
    books = Book.query.order_by(Book.title, Book.author).all()
    return render_template("list-books.html", books=books)


@main.get("/search-books")
@main.get("/search-books.html")
@login_required
def search_books():
    query = request.args.get("q", "").strip()
    books = []
    if query:
        pattern = f"%{query}%"
        books = Book.query.filter(
            or_(Book.title.ilike(pattern), Book.author.ilike(pattern), Book.isbn.ilike(pattern))
        ).order_by(Book.title, Book.author).all()
        db.session.add(
            Search(user_id=session["user_id"], query=query, results=[book.id for book in books])
        )
        db.session.commit()
    return render_template("search-books.html", books=books, query=query)


@main.route("/issue-book", methods=["GET", "POST"])
@main.get("/issue-book.html")
@login_required
def issue_book():
    available_books = Book.query.filter(
        ~Book.issues.any(Issue.return_date.is_(None))
    ).order_by(Book.title, Book.author).all()
    if request.method == "POST":
        try:
            book_id = int(request.form.get("book_id", ""))
        except ValueError:
            flash("Select a valid book to borrow.", "error")
            return redirect(url_for("main.issue_book"))
        book = db.session.get(Book, book_id)
        if not book:
            flash("That book is no longer available.", "error")
        elif Issue.query.filter_by(book_id=book.id, return_date=None).first():
            flash("That book is already checked out.", "error")
        else:
            db.session.add(Issue(user_id=session["user_id"], book_id=book.id))
            db.session.commit()
            flash("Book checked out successfully.", "success")
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("main.issue_book"))
    return render_template("issue-book.html", books=available_books)


@main.get("/view-issued-books")
@main.get("/view-issued-books.html")
@main.get("/issued-books")
@login_required
def view_issued_books():
    issues = Issue.query.filter_by(
        user_id=session["user_id"], return_date=None
    ).order_by(Issue.issue_date.desc()).all()
    return render_template("view-issued-books.html", issues=issues)


@main.post("/return-book/<int:issue_id>")
@login_required
def return_book(issue_id):
    issue = Issue.query.filter_by(
        id=issue_id, user_id=session["user_id"], return_date=None
    ).first_or_404()
    issue.return_date = utc_now()
    elapsed_days = (issue.return_date - issue.issue_date).days
    issue.fine_amount = max(0, elapsed_days - 14) * Decimal("0.50")
    db.session.commit()
    flash("Book returned successfully.", "success")
    return redirect(url_for("main.view_issued_books"))


@main.get("/fine-calculator")
@main.get("/fine-calculator.html")
@login_required
def fine_calculator():
    return render_template("fine-calculator.html")
