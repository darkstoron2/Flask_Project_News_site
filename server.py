import os
import flask_login
from flask import Flask, render_template, redirect
from flask_restful import Api
from itsdangerous import URLSafeTimedSerializer
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from data import db_session
from data.news import News
from data.users import User
from flask_login import LoginManager, login_user, login_required, logout_user
from requests import get, post, put, delete
from data.users_resource import UserResource, UserListResource
from forms.add_news import AddNewsForm
from forms.login import LoginForm
from forms.register import RegisterForm
from data.news_resource import NewsResource, NewsListResource
from geocoder import find_a_town

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/img'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_serializer = URLSafeTimedSerializer(app.secret_key)


@app.route('/news/<int:news_id>')
def news(news_id):  # Показ новости
    param = {}
    # Забираем новость из api
    news = get(f'http://localhost:5000/api/v2/news/{news_id}').json()['news']
    param['news'] = news
    #  Проверяем наличие картинки
    if news['img'] is None or news['img'] == '':
        param['img'] = '/static/img/plug.png'
    else:
        param['img'] = f'/static/img/{news["id"]}/{news["img"]}'
    #  Проверяем наличие адреса и отправляем запрос в геокодрер на создание снимка места
    if find_a_town(news['address']):
        param['address'] = '/static/img/map.png'
    else:
        param['address'] = '/static/img/plug.png'
    return render_template('news_show.html', **param)


@app.route('/')
def news_table():
    # Главная страница с новостями
    user = flask_login.current_user
    news = get('http://localhost:5000/api/v2/news').json()
    # Проверяем заргестрирован ли наш пользователь, ведь эту страницу могут посетить и анонимы
    if user.is_authenticated:
        # Сортируем новости по его любимому тэгу
        news = sorted(news, key=lambda x: x['tags'] != user.favourite_tags)
        ok_news = []
        # Отсеиваем новости для несовершеннолетних
        if user.age < 18:
            for i in range(len(news)):
                if 'Криминал' not in news[i]['tags']:
                    ok_news.append(news[i])
        else:
            ok_news = news.copy()
    else:
        ok_news = news.copy()
    return render_template('news_table.html', title='News', news=ok_news)


@app.route('/delete_news/<int:news_id>',  methods=['GET', 'POST'])
@login_required
def delete_news(news_id):
    # Удаление новости через Api
    news = get(f'http://localhost:5000/api/v2/news/{news_id}').json()['news']
    # Проверяем авторство статьи
    if flask_login.current_user.id != news['user']['id']:
        return render_template('error.html', error='Вы не автор этой новости')
    else:
        delete(f'http://localhost:5000/api/v2/news/{news_id}').json()
        return redirect('/')


@app.route('/edit_news/<int:news_id>',  methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    # Изменение новости
    # Забираем новость из api
    news = get(f'http://localhost:5000/api/v2/news/{news_id}').json()['news']
    # Проверяем авторство статьи
    if flask_login.current_user.id != news['user']['id']:
        return render_template('error.html', error='Вы не автор этой новости')
    else:
        form = AddNewsForm()  # Создаем форму
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Проверяем, чтобы пользователь не создал новость с одним и тем же именем
            if db_sess.query(News).filter(News.title == form.title.data).first() and news['title'] != form.title.data:
                return render_template('add_news.html', title='Изменение новости',
                                       form=form, message='Такая новость уже есть')
            # Если в новости появился файл, то создаем для него папку и сохраняем
            if form.img.data.filename != '' and news['img'] != form.img.data.filename:
                f = form.img.data
                filename = secure_filename(f.filename)
                if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], str(news_id))):
                    os.mkdir(path=os.path.join(app.config['UPLOAD_FOLDER'], str(news_id)))
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], str(news_id), filename))
            else:
                filename = news['img']
            # Если в новости появилась дата, то обновляем ее
            if form.created_date.data is None:
                form.created_date.data = news['created_date']
            # Отправляем запрос в api
            if 'error' in put(f'http://localhost:5000/api/v2/news/{news_id}', json={
                'title': form.title.data,
                'content': form.content.data,
                'user_id': flask_login.current_user.id,
                'tags': form.tags.data,
                'address': form.address.data,
                'img': filename,
                'created_date': str(form.created_date.data)
            }).json():
                return render_template('add_news.html', title='Изменение новости',
                                       form=form, message='Неверно заполнено')
            return redirect('/')
        # Графы img и created_date нет, т.к MultiDict не позволяет автозаполнить эти поля
        # Автозаполняем форму имеющимися данными
        form = AddNewsForm(MultiDict([('title', news['title']),
                                      ('content', news['content']),
                                      ('address', news['address']),
                                      ('tags', news['tags']),
                                      ('address', news['address'])]))
        return render_template('add_news.html', title='Изменение новости',
                               form=form)


@app.route('/add_news',  methods=['GET', 'POST'])
@login_required
def add_news():
    # Создание новости
    # Проверяем что пользователь Автор и может создавать новости
    if flask_login.current_user.is_admin:
        form = AddNewsForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            # Проверяем на повторяющиеся новости
            if db_sess.query(News).filter(News.title == form.title.data).first():
                return render_template('add_news.html', title='Добавление новости',
                                       form=form, message='Такая новость уже есть')
            # Если есть файл, то вытаскиваем имя, дальше создадим папку
            if form.img.data.filename != '':
                f = form.img.data
                filename = secure_filename(f.filename)
            else:
                filename = None
            # Отправляем запрос в api
            if 'error' in post('http://localhost:5000/api/v2/news', json={
                'title': form.title.data,
                'content': form.content.data,
                'user_id': flask_login.current_user.id,
                'tags': form.tags.data,
                'address': form.address.data,
                'img': filename,
                'created_date': str(form.created_date.data)
            }).json():
                return render_template('add_news.html', title='Добавление новости',
                                       form=form, message='Неверно заполнено')
            # Теперь, когда новость точно создалась, то создадим папку и сохраним картинку
            if form.img.data.filename != '':
                new = get('http://localhost:5000/api/v2/news').json()[-1]
                os.mkdir(path=os.path.join(app.config['UPLOAD_FOLDER'], str(new['id'])))
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], str(new['id']), filename))
            return redirect('/')
        return render_template('add_news.html', title='Добавление новости',
                               form=form)
    else:
        return render_template('error.html', error='Вы не админ')


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Изменение пользователя
    user = get(f'http://localhost:5000/api/v2/user/{user_id}').json()['user']  # Достаем пользователя из api
    # Если пользователя пытается изменить другой пользователя
    if flask_login.current_user.id != user_id:
        return render_template('error.html', error='Вы не этот пользователь')
    else:
        # Создаем форму
        form = RegisterForm()
        if form.validate_on_submit():
            if form.password.data != form.password_again.data:
                return render_template('register.html', title='Изменение пользователя',
                                       form=form,
                                       message="Пароли не совпадают")
            db_sess = db_session.create_session()
            # Проверка, что пользователь использует почту, на которую не был зарегестрирован другой юзер
            if db_sess.query(User).filter(User.email == form.email.data).first() and user['email'] != form.email.data:
                return render_template('register.html', title='Изменение пользователя',
                                       form=form,
                                       message="Такой пользователь уже есть")
            # Проверка на изменение пароля
            if form.password.data != user['hashed_password']:
                password = form.password.data
            else:
                password = None
            # Запрос в api
            if 'error' in put(f'http://localhost:5000/api/v2/user/{user_id}', json={
                'name': form.name.data,
                'surname': form.surname.data,
                'email': form.email.data,
                'age': form.age.data,
                'favourite_tags': form.favourite_tags.data,
                'speciality': form.speciality.data,
                'password': password,
                'is_admin': True if form.is_admin.data == 'Да' else False
            }).json().keys():
                return render_template('register.html', title='Изменение пользователя',
                                       form=form,
                                       message="Неверно заполнено")
            return redirect('/login')
        # Автозаполнение формы имеющимися данными.
        # Гружу hashed_password потому что другого пароля у меня нет, а заполнить поле нужно
        form = RegisterForm(MultiDict([('name', user['name']), ('surname', user['surname']),
                                       ('email', user['email']), ('age', user['age']),
                                       ('favourite_tags', user['favourite_tags']), ('speciality', user['speciality']),
                                       ('is_admin', "Да" if user['is_admin'] == 1 else "Нет"),
                                       ('password', user['hashed_password']),
                                       ('password_again', user['hashed_password'])]))
        return render_template('register.html', title='Изменение пользователя', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    # Регистрация
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if 'error' in post('http://localhost:5000/api/v2/user', json={
            'name': form.name.data,
            'surname': form.surname.data,
            'email': form.email.data,
            'age': form.age.data,
            'favourite_tags': form.favourite_tags.data,
            'speciality': form.speciality.data,
            'password': form.password.data,
            'is_admin': True if form.is_admin.data == 'Да' else False
        }).json().keys():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Неверно заполнено")
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Вход
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


def main():
    api.add_resource(NewsListResource, '/api/v2/news')
    api.add_resource(NewsResource, '/api/v2/news/<int:news_id>')
    api.add_resource(UserListResource, '/api/v2/user')
    api.add_resource(UserResource, '/api/v2/user/<int:user_id>')
    db_session.global_init("db/newspaper.db")
    app.run()


if __name__ == '__main__':
    main()
