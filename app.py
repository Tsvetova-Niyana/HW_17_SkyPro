# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False}
db = SQLAlchemy(app)

api = Api(app)
ns_movies = api.namespace("movies")
ns_directors = api.namespace("directors")
ns_genre = api.namespace("genres")


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class GenreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)


class DirectorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)


class MovieSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    genre = fields.Pluck(field_name="name", nested=GenreSchema)
    director_id = fields.Int()
    director = fields.Pluck(field_name="name", nested=DirectorSchema)


movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)


@ns_movies.route("/")
class MovieView(Resource):
    def get(self):
        """/movies — возвращает список всех фильмов, разделенный по страницам

            Доработайте представление так, чтобы оно возвращало только фильмы с
            определенным режиссером по запросу типа /movies/?director_id=1

            Доработайте представление так, чтобы оно возвращало только фильмы определенного жанра
            по запросу типа /movies/?genre_id=1

            Доработайте представление так, чтобы оно возвращало только фильмы с определенным режиссером и
            жанром по запросу типа /movies/?director_id=2&genre_id=4
        """
        director_id = request.args.get("director_id")
        genre_id = request.args.get("genre_id")
        page = request.args.get("page")

        if not director_id and not genre_id:
            movies = Movie.query.all()

        if director_id:
            movies = Movie.query.filter_by(director_id=director_id)

        if genre_id:
            movies = Movie.query.filter_by(genre_id=genre_id)

        if director_id and genre_id:
            movies = Movie.query.filter_by(director_id=director_id, genre_id=genre_id)

        if page:
            movies = Movie.query.paginate(int(page), 10).items

        return movies_schema.dump(movies), 200

    def post(self):
        """POST /movies/ —  добавляет кино в фильмотеку"""
        movie_data = request.json
        new_movie = Movie(**movie_data)

        with db.session.begin():
            db.session.add(new_movie)
        return "Запись добавлена", 201


@ns_movies.route("/<int:mid>")
class MovieView(Resource):
    def get(self, mid):
        """/movies/<id> — возвращает подробную информацию о фильме"""
        movie = Movie.query.get(mid)
        return movie_schema.dump(movie)

    def put(self, mid):
        """PUT /movies/<id> —  обновляет кино"""
        movie_data = request.json
        movie = Movie.query.get(mid)

        if movie:
            movie.title = movie_data.get("title")
            movie.description = movie_data.get("description")
            movie.trailer = movie_data.get("trailer")
            movie.year = movie_data.get("year")
            movie.rating = movie_data.get("rating")
            movie.genre_id = movie_data.get("genre_id")
            movie.director_id = movie_data.get("director_id")

            db.session.commit()
            return "", 204
        else:
            return "Запись не найдена", 404

    def delete(self, mid):
        """DELETE /movies/<id> —  удаляет кино"""
        movie = Movie.query.get(mid)

        if movie:
            db.session.delete(movie)
            db.session.commit()
            return "", 204
        else:
            return "Запись не существует", 404


@ns_directors.route("/")
class DirectorsView(Resource):
    def get(self):
        """/directors/ — возвращает всех режиссеров"""
        directors = Director.query.all()
        return directors_schema.dump(directors), 200

    def post(self):
        directors_data = request.json
        new_directors = Director(**directors_data)
        with db.session.begin():
            db.session.add(new_directors)
        return "Запись добавлена", 201


@ns_directors.route("/<int:did>")
class DirectorsView(Resource):
    def get(self, did):
        """/directors/<id> — возвращает подробную информацию о режиссере"""
        director = Director.query.get(did)
        if director:
            return director_schema.dump(director), 200
        else:
            return "Запись не найдена", 404

    def put(self, did):
        director_data = request.json
        director = Director.query.get(did)

        if director:
            director.name = director_data.get("name")

            db.session.commit()
            return "", 204
        else:
            return "Запись не найдена", 404

    def delete(self, did):
        director = Director.query.get(did)

        if director:
            db.session.delete(director)
            db.session.commit()

            return "", 204
        else:
            return "Запись не найдена", 404


@ns_genre.route("/")
class GenreView(Resource):
    def get(self):
        """/genres/ —  возвращает всех режиссеров"""
        genres = Genre.query.all()
        return genres_schema.dump(genres)

    def post(self):
        genres_data = request.json
        new_genres = Genre(**genres_data)
        with db.session.begin():
            db.session.add(new_genres)
        return "Запись добавлена", 201


@ns_genre.route("/<int:gid>")
class GenreView(Resource):
    def get(self, gid):
        """/genres/<id> — возвращает информацию о жанре с перечислением списка фильмов по жанру"""
        genre = Genre.query.get(gid)

        if genre:
            return genre_schema.dump(genre)
        else:
            return "Запись не найдена", 404

    def put(self, gid):
        genre_data = request.json
        genre = Genre.query.get(gid)

        if genre:
            genre.name = genre_data.get("name")

            db.session.commit()

            return "", 204
        else:
            return "Запись не найдена", 404

    def delete(self, gid):
        genre = Genre.query.get(gid)

        db.session.delete(genre)
        db.session.commit()

        return "", 204


if __name__ == '__main__':
    app.run(debug=True)
