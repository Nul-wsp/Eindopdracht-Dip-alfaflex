# AlfaFlix — eindopdracht DiP2

Een uitgewerkte Python/Flask-app voor een fysieke DVD-videotheek. Gebaseerd op het aangeleverde startproject. Met accounts, lenen, terugbrengen, reserveren, CRUD-API, Swagger, logging en een beheerdersrol. De originele opdracht staat in `original/`.

## 1. Openen in Visual Studio Code (Windows)

1. Pak de hele ZIP uit. Werk niet rechtstreeks in het ZIP-bestand.
2. Open VS Code. Kies **File → Open Folder** en selecteer de map `AlfaFlix`, waarin `app.py` staat.
3. Kies **Terminal → New Terminal**.
4. Controleer Python: `py --version`. Gebruik Python 3.11 of nieuwer.
5. Voer deze opdrachten één voor één uit:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

6. Laat de terminal open. Open **http://127.0.0.1:5000** in je browser.
7. Klik op **Account maken**, vul een gebruikersnaam en een wachtwoord van minimaal acht tekens in, registreer en log in.
8. Je ziet nu de collectie met zes voorbeeld-DVD's. Deze worden alleen bij de eerste start toegevoegd.

Stoppen: druk in de terminal op **Ctrl+C**. Opnieuw starten: alleen de laatste opdracht uitvoeren. Je accounts en wijzigingen blijven bewaard in `instance/videotheek.db`.

Op macOS/Linux: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt` en `.venv/bin/python app.py`.

## 2. Beheerder aanmaken

Open een tweede terminal in dezelfde map en voer uit:

```powershell
.\.venv\Scripts\python.exe -m flask --app app create-admin
```

Kies een **nieuwe** gebruikersnaam (bijvoorbeeld `beheerder`) en een sterk wachtwoord. Tijdens typen van het wachtwoord verschijnen geen tekens; dit is normaal. Bevestig het wachtwoord. Er bestaat geen vooraf ingesteld adminwachtwoord.

Log via de website in met deze beheerder. Nu verschijnt **Beheer**. Je kunt daar DVD's toevoegen en verwijderen. Onder **Collectie → Bewerken** kun je titel, genre, jaar, omschrijving en TMDB-film-ID aanpassen. Alle CRUD-handelingen in de browser gebruiken de API; er is geen aparte Create/Delete-formulierroute.

## 3. Functies gebruiken

| Actie | Waar / gedrag |
|---|---|
| Collectie bekijken | Alleen na inloggen; zoek op titel of genre en filter op status. |
| Lenen | Klik op Lenen bij een beschikbare DVD. Status wordt uitgeleend. |
| Terugbrengen | Alleen door de lener of een beheerder. Status wordt beschikbaar. |
| Reserveren | Alleen ingelogd, alleen bij een beschikbare DVD. Status wordt gereserveerd. |
| Ophalen | Annuleer eerst de reservering en leen de DVD daarna uit. Een gereserveerde DVD is altijd geblokkeerd voor lenen. |
| Annuleren | Alleen door de reserveerder of een beheerder. |
| Geschiedenis | Klant ziet eigen acties; beheerder ziet alle acties en wie ze uitvoerde. |
| Verwijderen | Alleen beheerder en alleen als beschikbaar. Historische logregels blijven bewaard. |

Elk filmrecord vertegenwoordigt **één fysiek DVD-exemplaar**. Meerdere exemplaren kunnen als aparte records met dezelfde titel worden toegevoegd. Er zijn geen betalingen, huurtermijnen of automatische vervaldata; dat vraagt de opdracht niet.

## 4. Externe API activeren — keuze 2

Zonder token werken de accounts, verhuur, reserveringen, logging en CRUD al. Er worden dan lokale tekstomschrijvingen en grafische titelkaarten getoond. Dat zijn geen opgehaalde TMDB-gegevens.

1. Maak een eigen account bij https://www.themoviedb.org/ en vraag toegang tot de API aan via je accountinstellingen.
2. Kopieer het **API Read Access Token** (de lange Bearer-tokenwaarde).
3. Kopieer `.env.example` naar `.env` in dezelfde map als `app.py`.
4. Vul in `.env` de regel `TMDB_TOKEN=jouw_lange_token` in. Zet er niet ook het woord `Bearer` voor.
5. Stop de app met Ctrl+C en start opnieuw.
6. Log in als beheerder. Ga naar **Collectie → Filmgegevens ophalen** bij bijvoorbeeld The Matrix. De voorbeeldfilms bevatten al een TMDB-film-ID.
7. De app haalt een Nederlandse omschrijving en een poster op. Open **Over deze film** om de omschrijving te zien. Gegevens worden in SQLite bewaard.
8. Bij een eigen film: vul via **Bewerken** eerst het juiste numerieke TMDB-film-ID in. Gebruik het nummer uit de TMDB-film-URL.

De server heeft internet nodig voor de API; de browser voor de poster. Bij een ontbrekend token, time-out, onjuist ID of ontbrekende poster/omschrijving verschijnt een melding en blijven bestaande gegevens bewaard. TMDB is met gesimuleerde antwoorden getest; een live controle met jouw eigen token moet nog worden uitgevoerd.

## 5. API en Swagger

Open **http://127.0.0.1:5000/api/docs**. De documentatie komt uit `swagger.yaml`. Log eerst op dezelfde host in via de website. Gebruik daarna **Try it out** en **Execute**. Swagger gebruikt de sessiecookie en haalt automatisch het CSRF-token op. Gebruik overal dezelfde hostnaam; wissel niet tussen localhost en 127.0.0.1.

| Methode | Endpoint | Toegang |
|---|---|---|
| GET | `/api/csrf` | Iedereen; geeft CSRF-token en sessiecookie |
| GET | `/api/films` | Ingelogd; optioneel `?q=matrix&status=beschikbaar` |
| GET | `/api/films/1` | Ingelogd |
| POST | `/api/films` | Beheerder; nieuwe DVD |
| PATCH | `/api/films/1` | Beheerder; filmgegevens wijzigen |
| DELETE | `/api/films/1` | Beheerder; beschikbare DVD verwijderen |
| POST | `/api/films/1/lenen` | Ingelogd; alleen beschikbaar |
| POST | `/api/films/1/terugbrengen` | Eigen lener of beheerder |
| POST | `/api/films/1/reserveren` | Ingelogd; alleen beschikbaar |
| POST | `/api/films/1/annuleren` | Eigen reserveerder of beheerder |
| POST | `/api/films/1/tmdb` | Beheerder; token en film-ID vereist |
| GET | `/api/logs` | Eigen acties; admin alle acties |

Voor een andere API-client: haal eerst `/api/csrf` op, bewaar de cookie en stuur de tokenwaarde in `X-CSRF-Token` mee met iedere POST/PATCH/DELETE. Login via `POST /login` als formulier met `username`, `password` en `csrf_token`. Na login wordt het token vernieuwd; haal het opnieuw op. De API heeft bewust geen onbeveiligde CRUD-endpoints.

Voorbeeld-JSON om als beheerder een DVD aan te maken:

```json
{"title":"Mijn nieuwe film","genre":"Drama","year":2024,"description":"Een korte omschrijving.","tmdb_id":null}
```

Foutcodes: **400** ongeldige invoer/CSRF, **401** niet ingelogd, **403** geen rechten, **404** niet gevonden, **409** statusconflict, **502** externe API-fout, **503** TMDB niet ingesteld.

## 6. Documenten en opbouw

- `assessment.md`: ingevuld overzicht van gemaakte onderdelen en verwijzingen.
- `docs/Stroomschema.svg`: stroomschema reserveren, 15 stappen, met standaardsymbolen.
- `docs/Uitleg_stroomschema.md`: uitleg van iedere stap.
- `docs/Technische_uitleg.md`: architectuur, database, beveiliging, code-uitleg en ERD.
- `docs/Demonstratie_en_inleveren.md`: handmatig demonstreren, screenshots en GitHub-inleverstappen.
- `docs/Testresultaten.md`: daadwerkelijk uitgevoerde controles en resterende beperkingen.
- `tests/test_app.py`: automatische tests met afzonderlijke tijdelijke databases.
- `original/Eindopdracht.docx`: originele schoolopdracht.

De startdatabase uit het oorspronkelijke project had geen gebruikers/eigenaars. Deze uitwerking maakt een nieuwe database in `instance/` met het schema uit `schema.sql`. Er is geen migratie van een oude database nodig: de aangeleverde ZIP bevatte geen database.

## 7. Tests uitvoeren

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

De tests gebruiken tijdelijke databases en wijzigen je eigen collectie niet.

## 8. Veelvoorkomende problemen

- **No module named flask**: installeer de requirements met exact dezelfde `.venv`-Python als waarmee je de app start.
- **Pagina opent niet**: start `app.py` en houd de terminal open. Controleer de URL en foutmelding in de terminal.
- **Poort 5000 bezet**: sluit de eerder gestarte app. Eventueel: `.\.venv\Scripts\python.exe -m flask --app app run --port 5001` en open poort 5001.
- **CSRF-melding**: vernieuw de pagina en log zo nodig opnieuw in. Een oude tab kan nog een oud token bevatten.
- **Bestaande naam bij create-admin**: kies een nieuwe naam. Registratie maakt altijd een gewone gebruiker.
- **TMDB werkt niet**: controleer het Read Access Token in `.env`, herstart de app en controleer het film-ID.
- **Opmaak of Swagger ontbreekt**: controleer of de map `static/vendor` volledig is uitgepakt. Bootstrap en Swagger UI worden lokaal meegeleverd; hiervoor is geen internet nodig.

De app start lokaal met debug uit. Voor publieke hosting zijn onder andere HTTPS, een geschikte WSGI-server en aanvullende maatregelen zoals login-rate-limiting nodig. Dit pakket is bedoeld voor de lokale schoolopdracht.
