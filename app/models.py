from db import db, ma


class LogData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(), nullable=False)
    ms = db.Column(db.Integer)
    timestamp = db.Column(db.Integer)

    def __init__(self, method, ms, timestamp):
        self.method = method
        self.ms = ms
        self.timestamp = timestamp


def get_log_data():
    return LogData.query.all()


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    author = db.Column(db.String(120))

    def __init__(self, title, author):
        self.title = title
        self.author = author


class BooksSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        ordered = True


book_schema = BooksSchema()
books_schema = BooksSchema(many=True)
