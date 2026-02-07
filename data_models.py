from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    date_of_death = db.Column(db.Date, nullable=True)
    books = db.relationship("Book", back_populates="author", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Author id={self.id!r} name={self.name!r}>"

    def __str__(self) -> str:
        return f"{self.name}"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    publication_year = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    author = db.relationship("Author", back_populates="books")

    def __repr__(self) -> str:
        return f"<Book id={self.id!r} title={self.title!r} isbn={self.isbn!r}>"

    def __str__(self) -> str:
        return f"{self.title}"
