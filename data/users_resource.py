from flask import jsonify
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.news import News
from data.users import User

parser = reqparse.RequestParser()
parser.add_argument('name', required=False)
parser.add_argument('surname', required=False)
parser.add_argument('email', required=False)
parser.add_argument('age', required=False, type=int)
parser.add_argument('password', required=False)
parser.add_argument('speciality', required=False)
parser.add_argument('is_admin', required=False, type=bool)
parser.add_argument('favourite_tags', required=False)


# Вывести ошибку если нет такого юзера
def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f"User {user_id} not found")


class UserResource(Resource):
    def get(self, user_id):
        # Получение юзера
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict(
            only=('name', 'surname', 'speciality', 'favourite_tags', 'age', 'id', 'email',
                  'hashed_password', 'is_admin'))})

    def delete(self, user_id):
        # Удаление юзера
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        session.delete(user)
        session.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        # Изменение юзера
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(User).get(user_id)
        args = parser.parse_args()
        user.name = args['name'] if args['name'] is not None else user.name
        user.surname = args['surname'] if args['surname'] is not None else user.surname
        user.age = args['age'] if args['age'] is not None else user.age
        user.email = args['email'] if args['email'] is not None else user.email
        user.is_admin = args['is_admin'] if args['is_admin'] is not None else user.is_admin
        user.speciality = args['speciality'] if args['speciality'] is not None else user.speciality
        user.favourite_tags = args['favourite_tags'] if args['favourite_tags'] is not None else user.favourite_tags
        if args['password'] is not None:
            user.set_password(args['password'])
        session.commit()
        return jsonify({'success': 'OK'})


class UserListResource(Resource):
    def get(self):
        # Получение юзеров
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('name', 'surname', 'speciality')) for item in users]})

    def post(self):
        # Создание юзера
        args = parser.parse_args()
        session = db_session.create_session()
        if not all(args[key] is not None for key in ['name', 'surname', 'age', 'email', 'password', 'favourite_tags',
                                                     'speciality', 'is_admin']):
            abort(404, message=f"Not all keys")
        user = User(
            name=args['name'],
            surname=args['surname'],
            age=args['age'],
            email=args['email'],
            speciality=args['speciality'],
            is_admin=args['is_admin'],
            favourite_tags=args['favourite_tags']
        )
        user.set_password(args['password'])
        session.add(user)
        session.commit()
        return jsonify({'success': 'OK'})