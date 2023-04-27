from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, IntegerField, SelectField, \
    RadioField
from wtforms.validators import DataRequired, Optional


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = StringField('Пароль', validators=[DataRequired()])
    password_again = StringField('Повторите пароль', validators=[DataRequired()])
    surname = StringField("Фамилия пользователя", validators=[DataRequired()])
    name = StringField("Имя пользователя", validators=[DataRequired()])
    age = IntegerField("Возраст", validators=[DataRequired()])
    speciality = StringField("Специальность пользователя", [Optional()])
    favourite_tags = SelectField("Интересующие темы", choices=['Спорт', 'IT', 'Бизнес', 'Криминал', 'Политика'],
                                 validators=[DataRequired()])
    is_admin = RadioField('Вы автор?', choices=['Да', 'Нет'], validators=[DataRequired()])
    submit = SubmitField('Войти')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)