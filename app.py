import os
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import or_
from data_models import Author, Book, db

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
)

db.init_app(app)

# Lightweight migration for the new rating column.
def ensure_rating_column() -> None:
    db_path = os.path.join(basedir, "data", "library.sqlite")
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("PRAGMA table_info(books)")
        columns = {row[1] for row in cursor.fetchall()}
        if "rating" not in columns:
            conn.execute("ALTER TABLE books ADD COLUMN rating INTEGER")
            conn.commit()
    finally:
        conn.close()


ensure_rating_column()

# One-time table creation (run once, then comment out if desired)
# with app.app_context():
#     db.create_all()


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    sort = request.args.get("sort", "title")
    message = request.args.get("message")
    books_query = Book.query
    joined_author = False

    if query:
        books_query = books_query.join(Author).filter(
            or_(
                Book.title.ilike(f"%{query}%"),
                Author.name.ilike(f"%{query}%"),
            )
        )
        joined_author = True

    if sort == "author":
        if not joined_author:
            books_query = books_query.join(Author)
        books_query = books_query.order_by(Author.name, Book.title)
    else:
        books_query = books_query.order_by(Book.title)

    books = books_query.all()
    no_results_message = (
        f"Keine Bucher gefunden fur: {query}" if query and not books else None
    )

    return render_template(
        "home.html",
        books=books,
        sort=sort,
        q=query,
        no_results_message=no_results_message,
        message=message,
    )


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    success_message = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birthdate_raw = request.form.get("birthdate") or None
        date_of_death_raw = request.form.get("date_of_death") or None

        birth_date = (
            datetime.strptime(birthdate_raw, "%Y-%m-%d").date()
            if birthdate_raw
            else None
        )
        date_of_death = (
            datetime.strptime(date_of_death_raw, "%Y-%m-%d").date()
            if date_of_death_raw
            else None
        )

        if name:
            author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death,
            )
            db.session.add(author)
            db.session.commit()
            success_message = f"Autor hinzugefugt: {author.name}"

    return render_template("add_author.html", success_message=success_message)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    success_message = None
    authors = Author.query.order_by(Author.name).all()

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        title = request.form.get("title", "").strip()
        publication_year_raw = request.form.get("publication_year", "").strip()
        rating_raw = request.form.get("rating", "").strip()
        author_id_raw = request.form.get("author_id", "").strip()

        publication_year = int(publication_year_raw) if publication_year_raw else None
        rating = int(rating_raw) if rating_raw else None
        author_id = int(author_id_raw) if author_id_raw else None

        if rating is not None and not (1 <= rating <= 10):
            rating = None

        if isbn and title and author_id:
            book = Book(
                isbn=isbn,
                title=title,
                publication_year=publication_year,
                rating=rating,
                author_id=author_id,
            )
            db.session.add(book)
            db.session.commit()
            success_message = f"Buch hinzugefugt: {book.title}"

    return render_template(
        "add_book.html",
        authors=authors,
        success_message=success_message,
    )


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id: int):
    book = Book.query.get_or_404(book_id)
    author = book.author

    db.session.delete(book)
    db.session.commit()

    if author:
        remaining = Book.query.filter_by(author_id=author.id).count()
        if remaining == 0:
            db.session.delete(author)
            db.session.commit()

    return redirect(url_for("home", message="Buch erfolgreich geloescht."))


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id: int):
    author = Author.query.get_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
    return redirect(url_for("home", message="Autor erfolgreich geloescht."))


@app.route("/book/<int:book_id>")
def book_detail(book_id: int):
    book = Book.query.get_or_404(book_id)
    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id: int):
    author = Author.query.get_or_404(author_id)
    return render_template("author_detail.html", author=author)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
