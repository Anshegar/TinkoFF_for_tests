'''
Задача:
На базе фрейм ворка Flask создать программу :

1) Создать схему таблиц БД (БД sqlite) для хранения ключевых ответов 
Табл №1 Тема - "theme" Содержит в себе:
--- id
--- Тема -  Столбец строка
---
Табл №2 Ответ - "answer" Содержит в себе 
--- id
--- Тег - Столбец со множеством, элементы которого - Ключевые слова для поиска(теги)
--- Ответ Столбец строка (само тело ответа)
--- FK(Внешний ключ) на id таблицы "theme"

2) Написать ФОРМУ внесения новой Темы, вверху будут выведены все существующие в таблице theme темы с их id
И принимающую для записи:
--- Новую тему для записи в таблицу theme

3) Написать ФОРМУ внесения новых Данных, вверху будут выведены все существующие в таблице theme темы с их id
И принимающую для записи:
--- ключевые слова, через запятую, из которых будет сформировано множество для столбца Тег таблицы answer
--- Ответ - сам ответ
--- FK(Внешний ключ) на id таблицы "theme". Можно внести как числом так и наименованием темы, (если прислали число то используем его для связи по id с theme сразу, если строкой, то ищем в theme тему с таким названием , и к его id соединяем FK поле answer)

--- Записываем данные в Базу данных.  

3) Написать Форму поиска данных по Темам + тегам \  вверху страницы выведены все существующие в таблице theme темы с их id
Поля ввода:
Тема (можно как названием так и id ) -  ключевой аргумент
теги через запятую - вторичный аргумент поиска

--- Вернет Основной ответ:      если есть тема с максимальным количеством соответсвующих тегов 
--- Вернет Вторичные ответы:    если есть тема + какоето кол во соответвующих тегов 
--- Вернет третичный ответ:     если нет темы , но есть соответсвующие темы  


'''


# 1. Создание схемы таблиц БД
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, render_template,url_for,redirect

# Формы
from flask import render_template, redirect, url_for, request


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
#app = Flask(__name__, template_folder='app/templates')
app.config['SECRET_KEY'] = 'mykey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Migrate(app,db)



# 1. Схема БД
class Theme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tags = db.Column(db.Text)
    answer = db.Column(db.Text)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'))
    theme = db.relationship('Theme', backref=db.backref('answers', lazy='dynamic'))





# 2. Форма для добавления новой темы

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('base.html')


@app.route('/add_theme', methods=['GET', 'POST'])
def add_theme():
    if request.method == 'POST':
        new_theme = request.form['new_theme']
        theme = Theme(name=new_theme)
        db.session.add(theme)
        db.session.commit()
        return redirect(url_for('add_theme'))
    
    themes = Theme.query.all()
    return render_template('add_theme.html', themes=themes)





# 3. Форма для добавления новых ответов
@app.route('/add_answer', methods=['GET', 'POST'])
def add_answer():
    if request.method == 'POST':
        tags = request.form['tags']
        answer = request.form['answer']
        theme_id = request.form['theme_id']
        
        theme = Theme.query.get(theme_id)
        new_answer = Answer(tags=tags, answer=answer, theme=theme)
        db.session.add(new_answer)
        db.session.commit()
        return redirect(url_for('add_answer'))
    
    themes = Theme.query.all()
    return render_template('add_answer.html', themes=themes)




# 4. Форма для поиска ответов
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        theme_id_or_name = request.form['theme']
        tags = request.form['tags'].split(',')
        
        theme = Theme.query.filter((Theme.id == theme_id_or_name) | (Theme.name == theme_id_or_name)).first()
        if theme:
            answers = theme.answers.filter(Answer.tags.contains(','.join(tags))).all()
            if answers:
                primary_answer = max(answers, key=lambda a: len(a.tags.split(',')))
                secondary_answers = [a for a in answers if a != primary_answer]
                return render_template('search.html', primary_answer=primary_answer, secondary_answers=secondary_answers)
        
        related_answers = Answer.query.filter(Answer.tags.contains(','.join(tags))).all()
        return render_template('search.html', related_answers=related_answers)
    
    themes = Theme.query.all()
    return render_template('search.html', themes=themes)



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)