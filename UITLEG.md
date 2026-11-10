# AlfaFlix: eenvoudige versie

Deze versie maakt alleen wat nodig is voor de verplichte onderdelen en keuze 1 (reserveren). De website heeft standaard Bootstrap-opmaak, een DVD-tabel en gewone formulieren. Er is één Python-bestand en geen eigen JavaScript voor de videotheek.

## Wat zit erin?

- Registreren, inloggen en uitloggen.
- DVD-overzicht dat alleen zichtbaar is na inloggen.
- Lenen, terugbrengen, reserveren en annuleren.
- Logging: welke gebruiker welke actie uitvoert en wanneer.
- Titel bewerken via de website en de API.
- DVD toevoegen en verwijderen alleen via de API.
- Swagger-documentatie in `swagger.yaml`.
- Een stroomschema met uitleg.

Er is geen TMDB-integratie, rollenverdeling, beheerpaneel, 2FA of OAuth. De opdracht vraagt minimaal één keuze: in deze versie is dat reserveren. Alle ingelogde gebruikers kunnen de titel wijzigen en via de API DVD's toevoegen/verwijderen. Voor deze schoolopdracht zijn geen gebruikersrollen gekozen.

## Bestanden

| Bestand | Wat doet het? |
|---|---|
| app.py | Alle Python-code: routes, database, inloggen en DVD-acties. |
| templates/base.html | Gemeenschappelijke navigatie en Bootstrap. |
| templates/home.html | Beginpagina. |
| templates/login.html | Inlogformulier. |
| templates/register.html | Registratieformulier. |
| templates/videotheek.html | Tabel met DVD's en actieknoppen. |
| templates/bewerken.html | Formulier om een titel te wijzigen. |
| templates/geschiedenis.html | Je eigen handelingen. |
| templates/api.html | Swagger-pagina. |
| templates/fout.html | Eenvoudige foutmelding met link terug. |
| swagger.yaml | Beschrijving van de API. |
| static/ | Meegeleverde Bootstrap- en Swagger-bestanden. Deze hoef je niet zelf te schrijven. |
| Stroomschema.svg | Reserveren in 15 stappen. Open in een browser. |
| Stroomschema_uitleg.md | Uitleg bij het schema. |
| assessment.md | Overzicht voor het inleveren. Vul je eigen gegevens in. |

`videotheek.db` en `sleutel.txt` worden automatisch gemaakt bij het starten. Deze staan in .gitignore en horen niet in GitHub. De database bevat je accounts en handelingen. Het sleutelbestand is nodig voor het ondertekenen van de sessiecookie.

## De Python-code begrijpen

Een route vertelt Flask wat er moet gebeuren als iemand een URL opent.

```python
@app.route('/')
def home():
    return render_template('home.html')
```

Bij de beginpagina wordt `home.html` getoond. De andere routes werken op dezelfde manier.

### GET en POST

GET gebruik je om een pagina of gegevens op te vragen. POST gebruik je om een formulier te versturen of een handeling uit te voeren. Een route met GET en POST kan eerst een formulier tonen en het daarna verwerken.

### De database

Er zijn drie tabellen:

| Tabel | Gegevens |
|---|---|
| gebruiker | id, gebruikersnaam en gehasht wachtwoord |
| film | id, title, status, gebruiker_id en verwijderd |
| logging | id, film_id, gebruiker_id, actie en tijd |

Een film is één fysiek DVD-exemplaar. `gebruiker_id` in film geeft aan wie hem leent of reserveert. Bij beschikbaar is dat veld leeg. Een logregel verwijst naar een film en de gebruiker die de handeling uitvoerde.

`database()` opent de database. `g` is een tijdelijke plek waar Flask de verbinding voor de huidige aanvraag bewaart. `sluit_database()` sluit die verbinding na de aanvraag.

In SQL gebruiken we vraagtekens voor waarden:

```python
db.execute('SELECT * FROM film WHERE id=?', (film_id,))
```

Zo geef je de invoer apart aan SQLite door. Je plakt de invoer niet in de SQL-tekst.

### Inloggen

Bij registratie wordt het wachtwoord gehasht met `generate_password_hash`. Dat betekent dat het oorspronkelijke wachtwoord niet leesbaar in de database staat. `check_password_hash` controleert het wachtwoord bij inloggen.

Na inloggen staan het gebruikers-ID en de naam in `session`. Flask onthoudt de sessie via een ondertekende cookie. Bij uitloggen wordt de sessie leeggemaakt. De videotheek controleert of het gebruikers-ID in de sessie staat.

### DVD-acties

`verwerk_actie()` wordt door zowel de website als de API gebruikt. Daar staat de controle voor lenen, terugbrengen, reserveren en annuleren.

| Huidige status | Actie | Nieuwe status |
|---|---|---|
| beschikbaar | lenen | uitgeleend |
| beschikbaar | reserveren | gereserveerd |
| uitgeleend | terugbrengen door lener | beschikbaar |
| gereserveerd | annuleren door reserveerder | beschikbaar |

Een gereserveerde DVD kan niemand lenen. Eerst moet de reserveerder annuleren. Daarna kan de DVD worden geleend. Een andere gebruiker mag jouw DVD niet terugbrengen of jouw reservering annuleren.

`BEGIN IMMEDIATE` zorgt ervoor dat twee aanvragen niet tegelijk dezelfde DVD kunnen vastleggen. `with db:` slaat de wijziging en de logregel samen op. Gaat er iets mis, dan worden ze allebei teruggedraaid. Dit kleine stuk voorkomt dubbele verhuur.

### Formuliertoken

`controleer_token()` maakt een willekeurige tokenwaarde in de sessie. Elk formulier stuurt deze mee in een verborgen veld. De server controleert of de waarde klopt. Dit beschermt wijzigingen tegen formulieren op andere websites. Swagger stuurt hetzelfde token in de header `X-CSRF-Token`.

### Templates

Iedere pagina begint met `{% extends 'base.html' %}`. Daardoor hoef je de navigatie en Bootstrap niet telkens opnieuw te schrijven. De eigen inhoud staat in `{% block content %}`.

In de videotheek loopt een `for`-lus door de films. Een `if` controleert de status en bepaalt welke knoppen zichtbaar zijn. De server controleert de regels opnieuw als iemand een knop gebruikt.

## API proberen

1. Log in en klik op API.
2. Open GET `/api/films`.
3. Klik op Try it out en Execute. Je ziet de lijst met films.
4. Open POST `/api/films` en gebruik bijvoorbeeld:

```json
{"title":"Een nieuwe film"}
```

5. Met PATCH `/api/films/{film_id}` verander je de titel met hetzelfde JSON-formaat.
6. Met DELETE `/api/films/{film_id}` verwijder je een beschikbare DVD.

Read is GET, Create is POST, Update is PATCH en Delete is DELETE. Verwijderen verbergt de DVD uit de collectie. De logregels blijven daardoor bewaard. De geschiedenis toont de huidige titel van de gekoppelde DVD.

Voor de actie-endpoints hoef je geen JSON in te vullen. Gebruik het film-ID en klik Execute. Foutcodes: 400 = ongeldige invoer/token, 401 = niet ingelogd, 403 = andere eigenaar, 404 = niet gevonden, 409 = verkeerde status.

## Zelf controleren

1. Open /videotheek zonder inloggen: je komt op /login.
2. Registreer, log in en bekijk de drie DVD's.
3. Leen een DVD: hij wordt uitgeleend.
4. Breng hem terug: hij wordt beschikbaar.
5. Reserveer: hij wordt gereserveerd en de knop Lenen verdwijnt.
6. Annuleer: de DVD wordt weer beschikbaar.
7. Open Mijn geschiedenis en bekijk de vier acties.
8. Wijzig een titel via Bewerken.
9. Voeg via Swagger een film toe, wijzig hem en verwijder hem.
10. Log met een tweede account in een privévenster in. Controleer dat dit account niet jouw uitgeleende DVD kan terugbrengen.

Dit is een eenvoudige lokale schoolapp. Lees de code en probeer de stappen zelf, zodat je bij je beoordeling kunt uitleggen wat er gebeurt.
