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
from flask import Flask, render_template, redirect, url_for, request, jsonify
from sqlalchemy import or_
from sqlalchemy import func


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
    
# Модель для связи "многие-ко-многим" между ответами и тегами
class AnswerTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    tag = db.Column(db.String(100))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'))
    theme = db.relationship('Theme', backref=db.backref('answers', lazy='dynamic'))
    tags = db.relationship('AnswerTag', backref='answer', lazy='dynamic')



@app.route('/base')
def base():
    themes = Theme.query.order_by(Theme.name).all()
    themes_with_index = [(index, theme) for index, theme in enumerate(themes)]
    return render_template('base.html', themes_with_index=themes_with_index)

@app.route('/tests')
def tests():
    all_answers_for_theme = Answer.query.filter(Answer.theme_id == 6).all()
    print(all_answers_for_theme)

    #Выведите все ответы, содержащие тег 'один':

    all_answers_with_tag = Answer.query.filter(Answer.tags.contains('один')).all()
    print(all_answers_with_tag)

    all_answers_with_theme_and_tag = Answer.query.filter(Answer.theme_id == 6, Answer.tags.contains('один')).all()
    print(all_answers_with_theme_and_tag)

    return redirect(request.referrer)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        theme_id = request.form.get('theme_id')
        tags = [tag.strip().lower() for tag in request.form.get('tags').split(',') if tag.strip()]
        

        if theme_id:
            main_results = Answer.query.filter(Answer.theme_id == theme_id).all()   
            # Получить все записи тегов из базы данных и привести их к нижнему регистру
            all_tags = [tag.tag.lower() for tag in AnswerTag.query.all()]

            # Найти пересечение тегов из формы и тегов из базы данных
            common_tags = set(tags).intersection(set(all_tags))
            print(tags, common_tags)

            # Фильтровать ответы по общим тегам
            secondary_results = [answer for answer in Answer.query.all() if any(tag.tag.lower() in common_tags for tag in answer.tags)]

            if tags:
                exact_results = [answer for answer in Answer.query.filter(Answer.theme_id == theme_id).all() if any(tag.tag.lower() in tags for tag in answer.tags)]
                exact_results.sort(key=lambda x: len(set([tag.tag.lower() for tag in x.tags]).intersection(set(tags))))
                exact_results.reverse()
            else:
                exact_results = []

            main_results.sort(key=lambda x: len(set([tag.tag.lower() for tag in x.tags]).intersection(set(tags))), reverse=True)
            secondary_results.sort(key=lambda x: len(set([tag.tag.lower() for tag in x.tags]).intersection(set(tags))), reverse=True)

            themes = Theme.query.all()
            themes_with_ids = [(theme.id, f"{theme.id} - {theme.name}") for theme in themes]
            if exact_results or main_results or secondary_results:
                return render_template('index.html', themes=themes, themes_with_ids=themes_with_ids, main_results=main_results, secondary_results=secondary_results, exact_results=exact_results)
    
    themes = Theme.query.all()
    themes_with_ids = [(theme.id, f"{theme.id} - {theme.name}") for theme in themes]
    return render_template('index.html', themes=themes, themes_with_ids=themes_with_ids)


# 2. Форма для добавления новой темы
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


# 3. Удаление 
@app.route('/delete_theme', methods=['GET', 'POST'])
def delete_theme():
    themes = Theme.query.all()
    themes_with_ids = [(theme.id, f"{theme.id} - {theme.name}") for theme in themes]
    return render_template('delete_theme.html', themes=themes, themes_with_ids=themes_with_ids)

# - Удаление темы по ID
@app.route('/delete_theme_by_id', methods=['POST'])
def delete_theme_by_id():
    theme_id = request.form['theme_id']
    theme = Theme.query.get(theme_id)
    if theme:
        db.session.delete(theme)
        db.session.commit()
        return "Тема успешно удалена"
    else:
        return "Такой темы не существует"

# - Удаление темы по Имени
@app.route('/delete_theme_by_name', methods=['POST'])
def delete_theme_by_name():
    theme_name = request.form['theme_name']
    theme = Theme.query.filter_by(name=theme_name).first()
    if theme:
        db.session.delete(theme)
        db.session.commit()
        return "Тема успешно удалена"
    else:
        return "Такой темы не существует"


@app.route('/update_theme', methods=['GET', 'POST'])
def update_theme():
    return render_template('update_theme.html')


# 5. Модификация темы по id
@app.route('/update_theme_by_id', methods=['POST'])
def update_theme_by_id():
    theme_id = request.form['theme_id']
    new_theme_name = request.form['new_theme_name']
    theme = Theme.query.get(theme_id)
    if theme:
        theme.name = new_theme_name
        db.session.commit()
        return "Тема успешно модифицирована"
    else:
        return "Такой темы не существует"

# 6. Модификация темы по имени
@app.route('/update_theme_by_name', methods=['POST'])
def update_theme_by_name():
    theme_name = request.form['theme_name']
    new_theme_name = request.form['new_theme_name']
    theme = Theme.query.filter_by(name=theme_name).first()
    if theme:
        theme.name = new_theme_name
        db.session.commit()
        return "Тема успешно модифицирована"
    else:
        return "Такой темы не существует"







# --------------------------------------------------------------!!!!


# 3. Форма для добавления новых ответов
@app.route('/add_answer', methods=['GET', 'POST'])
def add_answer():
    if request.method == 'POST':
        theme_name = request.form['theme_name']
        tags = [tag.strip() for tag in request.form['tags'].split(',') if tag.strip()]
        answer_text = request.form['answer_text']

        # Найдите или создайте тему
        theme = Theme.query.filter_by(name=theme_name).first()
        if not theme:
            theme = Theme(name=theme_name)
            db.session.add(theme)
            db.session.commit()

        # Создайте новый ответ
        new_answer = Answer(answer=answer_text, theme=theme)
        db.session.add(new_answer)

        # Добавьте теги для нового ответа
        for tag in tags:
            new_tag = AnswerTag(answer=new_answer, tag=tag)
            db.session.add(new_tag)

        db.session.commit()
        return redirect(url_for('add_answer'))

    themes = Theme.query.all()
    return render_template('add_answer.html', themes=themes)



@app.route('/delete_answer', methods=['GET', 'POST'])
def delete_answer():
    answers = Answer.query.all()
    answers_with_ids = [(answer.id, f"{answer.id} - {answer.answer}") for answer in answers]
    return render_template('delete_answer.html', answers=answers, answers_with_ids=answers_with_ids)

# Удаление ответа по ID
@app.route('/delete_answer_by_id', methods=['POST'])
def delete_answer_by_id():
    answer_id = request.form['answer_id']
    answer = Answer.query.get(answer_id)
    if answer:
        # Удалите связанные теги
        AnswerTag.query.filter_by(answer_id=answer.id).delete()
        db.session.delete(answer)
        db.session.commit()
        return "Ответ успешно удален"
    else:
        return "Такого ответа не существует"



#-----------------------------------------------------------!!!!
@app.route('/update_answer', methods=['GET', 'POST'])
def update_answer():
    if request.method == 'POST':
        answer_id = request.form['answer_id']
        theme_name = request.form['theme_name']
        tags_to_add = [tag.strip() for tag in request.form['tags_to_add'].split(',') if tag.strip()]
        tags_to_remove = [tag.strip() for tag in request.form['tags_to_remove'].split(',') if tag.strip()]
        answer_text = request.form['answer_text']

        # Найдите ответ по ID
        answer = Answer.query.get(answer_id)
        if answer:
            # Обновление данных ответа
            if theme_name:
                theme = Theme.query.filter_by(name=theme_name).first()
                if theme:
                    answer.theme = theme
                    
            if tags_to_add:
                for tag_name in tags_to_add:
                    existing_tag = AnswerTag.query.filter_by(answer_id=answer_id, tag=tag_name).first()
                    if not existing_tag:
                        new_tag = AnswerTag(answer_id=answer_id, tag=tag_name)
                        db.session.add(new_tag)

            if tags_to_remove:
                for tag_name in tags_to_remove:
                    tag_to_remove = AnswerTag.query.filter_by(answer_id=answer_id, tag=tag_name).first()
                    if tag_to_remove:
                        db.session.delete(tag_to_remove)

            if answer_text:
                answer.answer = answer_text

            db.session.commit()
            
            print("Ответ успешно обновлен")
            return redirect(url_for("update_answer"))
        else:
            print("Такого ответа не существует")
            return redirect(url_for("update_answer"))

    # Получите список всех тем для заполнения формы
    themes = Theme.query.all()
    return render_template('update_answer.html', themes=themes)





#-------------------------------------------------------------!!!!

# --- Форма для изменения Темы
# --- Форма в HTML будеn содержать уже заполненные поля взятые из БД, все кроме ID и 2 кнопки. 
# --- --- Изменить, отправит форму обратно в БД , надо будет сделать подтверждение
# --- --- Удалить, надо будет сделать подтверждение
# --- Форма для изменения ответов
# --- Форма в HTML будеn содержать уже заполненные поля взятые из БД, все кроме ID и 2 кнопки. 
# --- --- Изменить, отправит форму обратно в БД , надо будет сделать подтверждение
# --- --- Удалить, надо будет сделать подтверждение
 




# Форма для поиска ответов
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