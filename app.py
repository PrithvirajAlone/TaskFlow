import sqlite3
from unicodedata import category
from flask import Flask, render_template, request, redirect, url_for

#Create a Flask application instance
app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('tasks.db')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL CHECK (completed IN (0, 1))
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    columns = conn.execute(
    "PRAGMA table_info(tasks)"
    ).fetchall()

    if 'category_id' not in [column[1] for column in columns]:
        conn.execute('''
            ALTER TABLE tasks
            ADD COLUMN category_id INTEGER REFERENCES categories(id)
    ''')

    conn.commit()
    conn.close()

init_db()

def add_category(name):
    conn = sqlite3.connect('tasks.db')

    conn.execute(
        'INSERT INTO categories (name) VALUES (?)',
        (name,)
    )
    conn.commit()
    conn.close()

def get_categories():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        'SELECT * FROM categories ORDER BY name ASC'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_task(title):
    conn = sqlite3.connect('tasks.db')

    conn.execute(
      
    'INSERT INTO tasks (title, completed) VALUES (?, ?)',
    (title, 0)
)

    conn.commit()
    conn.close()
    


def get_tasks():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        'SELECT * FROM tasks ORDER BY id DESC'
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]

def get_tasks_by_category(category_id):
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        'SELECT * FROM tasks WHERE category_id = ? ORDER BY id DESC', (category_id,)
    ).fetchall()

    conn.close()
    return [dict(row) for row in row]





# Homepage route
@app.route('/',methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        
         task = request.form.get('task')
         if task:
            add_task(task)
            return redirect(url_for('home', _anchor='tasks'))
    
    tasks = get_tasks()
    total_tasks = len(tasks)

    completed_tasks = sum(1 for task in tasks if task['completed'])

    pending_tasks = total_tasks - completed_tasks

    if total_tasks > 0:
        progress = (completed_tasks / total_tasks) * 100
    else:
        progress = 0

    return render_template(
    'index.html',
    tasks=tasks,
    total_tasks=total_tasks,
    completed_tasks=completed_tasks,
    pending_tasks=pending_tasks,
    progress=progress
)

@app.route('/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id')

    conn = sqlite3.connect('tasks.db')
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/edit' , methods=['GET'])
def edit_task():
    task_id = request.args.get('task_id')

    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row

    task = conn.execute(
        'SELECT * FROM tasks WHERE id = ?',
        (task_id,)
    ).fetchone()

    conn.close()

    if task is None:
        return redirect(url_for('home'))

    return render_template('edit.html', task=task)

@app.route('/update' , methods=['POST'])
def update_task():
    task_id = request.form.get('task_id')
    new_title = request.form.get('title')

    if new_title:
        conn = sqlite3.connect('tasks.db')

        conn.execute(
            'UPDATE tasks SET title = ? WHERE id = ?',
            (new_title, task_id)
        )
        conn.commit()
        conn.close()

    return redirect(url_for('categories'))


@app.route('/complete', methods=['POST'])
def complete_task():
    task_id = request.form.get('task_id')
    completed = request.form.get('completed') == 'yes'

    conn = sqlite3.connect('tasks.db')

    conn.execute(
        'UPDATE tasks SET completed = ? WHERE id = ?',
        (int(completed), task_id)
    )

    conn.commit()
    conn.close()

    if request.form.get('return_to') == 'categories':
        return redirect(url_for('categories'))

    return redirect(url_for('home'))

@app.route('/statistics')
def statistics():
    tasks = get_tasks()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task['completed'])
    pending_tasks = total_tasks - completed_tasks

    if total_tasks > 0:
        progress = (completed_tasks / total_tasks) * 100
    else:
        progress = 0

    return render_template(
        'statistics.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress
    )

@app.route('/categories', methods=['GET', 'POST'])
def categories():

    if request.method == 'POST':
        name = request.form.get('category')

        if name:
            add_category(name)
            return redirect(url_for('categories'))

    all_categories = get_categories()

    for category in all_categories:

        # Get tasks belonging to this category
        category['tasks'] = get_tasks_by_category(category['id'])

        # Calculate task counts
        category['total_tasks'] = len(category['tasks'])

        category['completed_tasks'] = sum(
            1 for task in category['tasks'] if task['completed']
        )

        category['pending_tasks'] = (
            category['total_tasks'] - category['completed_tasks']
        )

        # Calculate completion percentage
        if category['total_tasks'] > 0:
            category['progress'] = (
                category['completed_tasks'] / category['total_tasks']
            ) * 100
        else:
            category['progress'] = 0

    return render_template(
        'categories.html',
        categories=all_categories
    )
@app.route('/delete-category',methods=['POST'])
def delete_category():
    category_id = request.form.get('category_id')

    conn = sqlite3.connect('tasks.db')

    conn.execute('UPDATE tasks SET category_id = NULL WHERE category_id = ?', (category_id,))
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))

    conn.commit()
    conn.close()
    return redirect(url_for('categories'))

@app.route('/add-category-task', methods=['POST'])
def add_category_task():
    task = request.form.get('task')
    category_id = request.form.get('category_id')

    if task and category_id:
        conn = sqlite3.connect('tasks.db')

        conn.execute(
            'INSERT INTO tasks (title, completed, category_id) VALUES (?, ?, ?)',
            (task, 0, category_id)
        )

        conn.commit()
        conn.close()

    return redirect(url_for('categories'))


# Run the application

if __name__ == '__main__':
    app.run(debug=True)
    

