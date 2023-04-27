import datetime

from flask import jsonify
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.news import News
from data.users import User

parser = reqparse.RequestParser()
parser.add_argument('title', required=False)
parser.add_argument('user_id', required=False, type=int)
parser.add_argument('tags', required=False)
parser.add_argument('content', required=False)
parser.add_argument('img', required=False)
parser.add_argument('address', required=False)
parser.add_argument('created_date', required=False)


# Если новости не нашлось, то выбрасываем ошибку
def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News {news_id} not found")


# Если новости не нашлось, то выбрасываем ошибку
def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        # Получение новости
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        return jsonify({'news': news.to_dict(
            only=('title', 'content', 'user', 'address', 'img', 'created_date', 'tags', 'id'))})

    def delete(self, news_id):
        # Удаление новости
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        session.delete(news)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, news_id):
        # Изменение новости
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        args = parser.parse_args()
        # Проверка на существование пользователя, который указан в новости
        if args['user_id'] is not None:
            abort_if_user_not_found(args['user_id'])
        if args['created_date'] != 'None':
            date = datetime.datetime.strptime(args['created_date'], '%Y-%m-%d %H:%M:%S')
        else:
            date = None
        news.title = args['title'] if args['title'] is not None else news.title
        news.user_id = args['user_id'] if args['user_id'] is not None else news.user_id
        news.tags = args['tags'] if args['tags'] is not None else news.tags
        news.content = args['content'] if args['content'] is not None else news.content
        news.address = args['address'] if args['address'] is not None else news.address
        news.img = args['img'] if args['img'] is not None else news.img
        news.created_date = date if date is not None else news.created_date
        session.commit()
        return jsonify({'success': 'OK'})


class NewsListResource(Resource):
    def get(self):
        # Получение новостей
        session = db_session.create_session()
        news = session.query(News).all()
        return jsonify([item.to_dict(
            only=('title', 'created_date', 'tags', 'user', 'id')) for item in news])

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        # Если в новости нету определенных ключей, то это ошибка в заполнении формы
        if not all(args[key] is not None for key in ['title', 'user_id', 'tags', 'content']):
            abort(404, message=f"Not all keys")
        # Если нет такого юзера вывести ошибку
        abort_if_user_not_found(args['user_id'])
        if args['created_date'] != 'None':
            date = datetime.datetime.strptime(args['created_date'], '%Y-%m-%d')
        else:
            date = None
        news = News(
            title=args['title'],
            content=args['content'],
            user_id=args['user_id'],
            tags=args['tags'],
            address=args['address'],
            img=args['img'],
            created_date=date
        )
        session.add(news)
        session.commit()
        return jsonify({'success': 'OK'})