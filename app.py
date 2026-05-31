from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import unquote
import json
import os
from datetime import datetime

app = Flask(__name__)

# Имя файла для хранения записей
DATA_FILE = 'diary_entries.json'


# Функция загрузки записей из JSON файла
def load_entries():
    if os.path.exists(DATA_FILE):
        # Проверяем, что файл не пустой
        if os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    entries = json.load(f)
                    # Проверяем, что загрузился словарь
                    if isinstance(entries, dict):
                        return entries
                    else:
                        return {}
                except json.JSONDecodeError:
                    return {}
        else:
            return {}
    else:
        # Файла нет - возвращаем пустой словарь
        return {}


# Функция сохранения записей в JSON файл
def save_entries(entries):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)


# Функция сортировки записей от новых к старым
def sort_entries_by_date(entries):
    """
    Сортирует записи по дате от новых к старым
    """
    if not entries:
        return {}

    # Преобразуем словарь в список кортежей (id, запись) и сортируем
    sorted_items = sorted(
        entries.items(),
        key=lambda x: x[1]['date'],  # Сортируем по полю date
        reverse=True  # reverse=True = от новых к старым (убывание)
    )
    # Преобразуем обратно в словарь (для сохранения порядка в Python 3.7+)
    return dict(sorted_items)


# Загружаем записи при старте приложения
diary_entries = load_entries()
# Сортируем записи при загрузке (если есть)
if diary_entries:
    diary_entries = sort_entries_by_date(diary_entries)
# Определяем следующий доступный ID
next_id = max(map(int, diary_entries.keys())) + 1 if diary_entries else 1


@app.route('/')
def blog():
    # Данные для таблицы (7 дисциплин)
    disciplines = [
        {
            'name': 'Python основы',
            'progress': '85%',
            'homework': '90%',
            'comments': 'Уверенное владение синтаксисом, функциями, ООП'
        },
        {
            'name': 'Flask фреймворк',
            'progress': '75%',
            'homework': '80%',
            'comments': 'Создание маршрутов, шаблонов, работа с формами'
        },
        {
            'name': 'HTML/CSS',
            'progress': '70%',
            'homework': '65%',
            'comments': 'В процессе изучения'
        },
        {
            'name': 'Базы данных (SQL)',
            'progress': '50%',
            'homework': '45%',
            'comments': 'Базовые запросы, JOIN'
        },
        {
            'name': 'Git и GitHub',
            'progress': '60%',
            'homework': '55%',
            'comments': 'Основные команды'
        },
        {
            'name': 'REST API',
            'progress': '30%',
            'homework': '25%',
            'comments': 'Изучаю концепции'
        },
        {
            'name': 'Docker',
            'progress': '20%',
            'homework': '15%',
            'comments': 'Планирую изучить'
        }
    ]

    return render_template('index.html', disciplines=disciplines)


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    global next_id, diary_entries
    message = None

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        date = request.form.get('date', '').strip()

        # Если дата не указана, ставим сегодняшнюю
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        if title and content:
            # Проверяем, нет ли уже записи с таким заголовком
            exists = False
            for entry in diary_entries.values():
                if entry['title'] == title:
                    exists = True
                    break

            if not exists:
                diary_entries[str(next_id)] = {
                    'title': title,
                    'content': content,
                    'date': date
                }
                # Сортируем записи после добавления
                diary_entries = sort_entries_by_date(diary_entries)
                save_entries(diary_entries)  # Сохраняем в файл
                next_id += 1
                message = f"✅ Запись '{title}' успешно добавлена!"
            else:
                message = f"⚠️ Запись с заголовком '{title}' уже существует!"
        else:
            message = "❌ Пожалуйста, заполните заголовок и текст записи!"

    # Записи уже отсортированы в global diary_entries
    return render_template('notes.html', entries=diary_entries, message=message,
                           today_date=datetime.now().strftime('%Y-%m-%d'))


@app.route('/delete/<int:entry_id>')
def delete_entry(entry_id):
    global diary_entries
    entry_id_str = str(entry_id)

    if entry_id_str in diary_entries:
        deleted_title = diary_entries[entry_id_str]['title']
        del diary_entries[entry_id_str]
        # Сохраняем изменения в файл
        save_entries(diary_entries)
        message = f"✅ Запись '{deleted_title}' удалена!"
    else:
        message = "❌ Запись не найдена!"

    return redirect(url_for('notes'))


@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    global diary_entries
    entry_id_str = str(entry_id)

    if entry_id_str not in diary_entries:
        return redirect(url_for('notes'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        date = request.form.get('date', '').strip()

        if title and content and date:
            diary_entries[entry_id_str] = {
                'title': title,
                'content': content,
                'date': date
            }
            # После редактирования сортируем записи заново
            diary_entries = sort_entries_by_date(diary_entries)
            save_entries(diary_entries)
            return redirect(url_for('notes'))

    entry = diary_entries[entry_id_str]
    return render_template('edit_note.html', entry=entry, entry_id=entry_id)


# Дополнительный маршрут для отображения статистики по записям
@app.route('/notes/stats')
def notes_stats():
    global diary_entries
    total_entries = len(diary_entries)

    if total_entries > 0:
        # Самая новая запись
        newest = list(diary_entries.values())[0] if diary_entries else None
        # Самая старая запись
        oldest = list(diary_entries.values())[-1] if diary_entries else None
    else:
        newest = None
        oldest = None

    return render_template('notes_stats.html',
                           total=total_entries,
                           newest=newest,
                           oldest=oldest)


if __name__ == '__main__':
    app.run(debug=True)