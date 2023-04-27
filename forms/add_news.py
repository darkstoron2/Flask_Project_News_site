from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import PasswordField, SubmitField, BooleanField, StringField, IntegerField, DateField, FileField, \
    validators, SelectField, DateTimeField
from wtforms.validators import DataRequired, Optional


class AddNewsForm(FlaskForm):
    title = StringField('Название новости', validators=[DataRequired()])
    tags = SelectField('Тема', choices=['Спорт', 'IT', 'Бизнес', 'Криминал', 'Политика'], validators=[DataRequired()])
    content = StringField('Текст новости', validators=[DataRequired()])
    address = StringField('Адрес проишествия (если есть)', [Optional()])
    created_date = DateField('Дата проишествия (по стандарту сегодняшняя дата)', [Optional()])
    img = FileField('Картинка к новости (если есть)', validators=[Optional()])
    submit = SubmitField('Добавить')
