from flask import Flask, render_template, request, redirect, session, flash, jsonify, g, abort, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
from pathlib import Path

app = Flask(__name__)
map_project = Path(__file__).resolve().parent
app.config['DATABASE'] = str(map_project / 'videotheek.db')

# De sleutel blijft bewaard, zodat je niet bij elke herstart uitlogt.
bestand_sleutel = map_project / 'sleutel.txt'
if not bestand_sleutel.exists():
    bestand_sleutel.write_text(secrets.token_hex(32))
app.secret_key = bestand_sleutel.read_text()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# Open een databaseverbinding voor deze aanvraag.
def database():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def sluit_database(fout):
    if 'db' in g:
        g.db.close()


# Maak de tabellen en drie voorbeeldfilms bij de eerste start.
def maak_database():
    nieuw = not Path(app.config['DATABASE']).exists()
    db = database()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS gebruiker (
            id INTEGER PRIMARY KEY,
            gebruikersnaam TEXT NOT NULL UNIQUE COLLATE NOCASE,
            wachtwoord TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS film (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'beschikbaar',
            gebruiker_id INTEGER REFERENCES gebruiker(id),
            verwijderd INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS logging (
            id INTEGER PRIMARY KEY,
            film_id INTEGER NOT NULL REFERENCES film(id),
            gebruiker_id INTEGER NOT NULL REFERENCES gebruiker(id),
            actie TEXT NOT NULL,
            tijd TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    if nieuw:
        db.executemany('INSERT INTO film (title) VALUES (?)',
                       [('The Matrix',), ('Finding Nemo',), ('The Lion King',)])
    db.commit()


# Een formulier mag alleen veranderen met het token uit onze eigen sessie.
@app.before_request
def controleer_token():
    if 'token' not in session:
        session['token'] = secrets.token_hex(32)
    if request.method in ['POST', 'PATCH', 'DELETE']:
        token = request.form.get('token') or request.headers.get('X-CSRF-Token', '')
        if not secrets.compare_digest(session['token'], token):
            abort(400, description='Vernieuw de pagina en probeer opnieuw.')


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(409)
def foutmelding(fout):
    if request.path.startswith('/api/'):
        return jsonify({'fout': fout.description}), fout.code
    return render_template('fout.html', fout=fout), fout.code


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        naam = request.form.get('gebruikersnaam', '').strip()
        wachtwoord = request.form.get('wachtwoord', '')
        if not 3 <= len(naam) <= 40 or not 8 <= len(wachtwoord) <= 128:
            flash('Naam: 3 tot 40 tekens. Wachtwoord: 8 tot 128 tekens.')
        else:
            db = database()
            bestaat = db.execute('SELECT id FROM gebruiker WHERE gebruikersnaam=?', (naam,)).fetchone()
            if bestaat:
                flash('Deze gebruikersnaam bestaat al.')
            else:
                db.execute('INSERT INTO gebruiker (gebruikersnaam, wachtwoord) VALUES (?, ?)',
                           (naam, generate_password_hash(wachtwoord)))
                db.commit()
                flash('Je account is gemaakt. Log nu in.')
                return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        naam = request.form.get('gebruikersnaam', '').strip()
        wachtwoord = request.form.get('wachtwoord', '')
        gebruiker = database().execute('SELECT * FROM gebruiker WHERE gebruikersnaam=?', (naam,)).fetchone()
        if gebruiker and len(wachtwoord) <= 128 and check_password_hash(gebruiker['wachtwoord'], wachtwoord):
            session.clear()
            session['gebruiker_id'] = gebruiker['id']
            session['naam'] = gebruiker['gebruikersnaam']
            return redirect('/videotheek')
        flash('Gebruikersnaam of wachtwoord is onjuist.')
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')


@app.route('/videotheek')
def videotheek():
    if 'gebruiker_id' not in session:
        return redirect('/login')
    films = database().execute('SELECT * FROM film WHERE verwijderd=0 ORDER BY title').fetchall()
    return render_template('videotheek.html', films=films)


# Dezelfde bewerking wordt door de website en API gebruikt.
def verander_titel(film_id, titel):
    if not isinstance(titel, str) or not 1 <= len(titel.strip()) <= 150:
        abort(400, description='Vul een titel van 1 tot 150 tekens in.')
    zoek_film(film_id)
    db = database()
    db.execute('UPDATE film SET title=? WHERE id=?', (titel.strip(), film_id))
    db.commit()


@app.route('/bewerken/<int:film_id>', methods=['GET', 'POST'])
def bewerken(film_id):
    if 'gebruiker_id' not in session:
        return redirect('/login')
    film = zoek_film(film_id)
    if request.method == 'POST':
        verander_titel(film_id, request.form.get('title', ''))
        return redirect('/videotheek')
    return render_template('bewerken.html', film=film)


def zoek_film(film_id):
    film = database().execute('SELECT * FROM film WHERE id=? AND verwijderd=0', (film_id,)).fetchone()
    if film is None:
        abort(404, description='DVD niet gevonden.')
    return film


# Controleer status, wijzig de DVD en voeg een logregel toe.
def verwerk_actie(film_id, actie):
    if actie not in ['lenen', 'terugbrengen', 'reserveren', 'annuleren']:
        abort(404, description='Onbekende actie.')
    db = database()
    # Voorkomt dat twee klanten tegelijk dezelfde DVD krijgen.
    with db:
        db.execute('BEGIN IMMEDIATE')
        film = zoek_film(film_id)
        if actie in ['lenen', 'reserveren']:
            if film['status'] != 'beschikbaar':
                abort(409, description='Deze DVD is niet beschikbaar.')
            status = 'uitgeleend' if actie == 'lenen' else 'gereserveerd'
            eigenaar = session['gebruiker_id']
        else:
            nodig = 'uitgeleend' if actie == 'terugbrengen' else 'gereserveerd'
            if film['status'] != nodig:
                abort(409, description='Deze actie past niet bij de status.')
            if film['gebruiker_id'] != session['gebruiker_id']:
                abort(403, description='Deze DVD is van een andere gebruiker.')
            status = 'beschikbaar'
            eigenaar = None
        db.execute('UPDATE film SET status=?, gebruiker_id=? WHERE id=?', (status, eigenaar, film_id))
        log_actie = 'huren' if actie == 'lenen' else actie
        db.execute('INSERT INTO logging (film_id, gebruiker_id, actie) VALUES (?, ?, ?)',
                   (film_id, session['gebruiker_id'], log_actie))


@app.route('/actie/<int:film_id>/<actie>', methods=['POST'])
def actie_website(film_id, actie):
    if 'gebruiker_id' not in session:
        return redirect('/login')
    verwerk_actie(film_id, actie)
    flash('Actie opgeslagen.')
    return redirect('/videotheek')


@app.route('/geschiedenis')
def geschiedenis():
    if 'gebruiker_id' not in session:
        return redirect('/login')
    regels = database().execute('''
        SELECT film.title, logging.actie, gebruiker.gebruikersnaam, logging.tijd
        FROM logging
        JOIN film ON film.id = logging.film_id
        JOIN gebruiker ON gebruiker.id = logging.gebruiker_id
        WHERE logging.gebruiker_id = ?
        ORDER BY logging.id DESC
    ''', (session['gebruiker_id'],)).fetchall()
    return render_template('geschiedenis.html', regels=regels)


# API: hier moet de gebruiker ook ingelogd zijn.
@app.before_request
def controleer_api_login():
    if request.path.startswith('/api/films') and 'gebruiker_id' not in session:
        abort(401, description='Log eerst in via de website.')


def film_json(film):
    return {'id': film['id'], 'title': film['title'], 'status': film['status']}


def json_invoer():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'title'}:
        abort(400, description='Stuur JSON met alleen het veld title.')
    return data


@app.route('/api/films', methods=['GET', 'POST'])
def api_films():
    db = database()
    if request.method == 'POST':
        titel = json_invoer()['title']
        if not isinstance(titel, str) or not 1 <= len(titel.strip()) <= 150:
            abort(400, description='Vul een titel van 1 tot 150 tekens in.')
        resultaat = db.execute('INSERT INTO film (title) VALUES (?)', (titel.strip(),))
        db.commit()
        return jsonify(film_json(zoek_film(resultaat.lastrowid))), 201
    films = db.execute('SELECT * FROM film WHERE verwijderd=0 ORDER BY title').fetchall()
    return jsonify([film_json(film) for film in films])


@app.route('/api/films/<int:film_id>', methods=['GET', 'PATCH', 'DELETE'])
def api_film(film_id):
    db = database()
    if request.method == 'PATCH':
        verander_titel(film_id, json_invoer()['title'])
    if request.method == 'DELETE':
        with db:
            db.execute('BEGIN IMMEDIATE')
            film = zoek_film(film_id)
            if film['status'] != 'beschikbaar':
                abort(409, description='Deze DVD is nog in gebruik.')
            # Bewaar de DVD intern, zodat de logregels blijven bestaan.
            db.execute('UPDATE film SET verwijderd=1 WHERE id=?', (film_id,))
        return '', 204
    return jsonify(film_json(zoek_film(film_id)))


@app.route('/api/films/<int:film_id>/<actie>', methods=['POST'])
def api_actie(film_id, actie):
    verwerk_actie(film_id, actie)
    return jsonify(film_json(zoek_film(film_id)))


@app.route('/api/docs')
def api_docs():
    return render_template('api.html')


@app.route('/swagger.yaml')
def swagger():
    return send_file(map_project / 'swagger.yaml')


with app.app_context():
    maak_database()

if __name__ == '__main__':
    app.run()
