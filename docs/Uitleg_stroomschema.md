# Uitleg stroomschema — DVD reserveren

Open `Stroomschema.svg` in een browser. Het schema bevat 15 stappen en hoort bij `POST /api/films/<film_id>/reserveren`. De browser stuurt deze aanvraag als de klant op **Reserveren** klikt.

## Symbolen

- Afgeronde rechthoek: start of einde.
- Parallellogram: invoer of uitvoer.
- Rechthoek: verwerking.
- Ruit: beslissing met een Ja- en Nee-uitgang.
- Pijl: volgorde van de stappen.

## Toelichting per stap

| Stap | Wat gebeurt er? | Koppeling met de code |
|---|---|---|
| 1 | Het proces begint. | Klant bekijkt de collectie. |
| 2 | De klant kiest een DVD en klikt Reserveren. Het DVD-ID gaat mee in de API-URL. | `static/app.js`: klikhandler; `api()` verstuurt POST. |
| 3 | Het systeem controleert of de sessie bij een ingelogde gebruiker hoort. | `login_required` in `app.py`. |
| 4 | Zonder login geeft de API 401. De gebruiker moet eerst inloggen. Er verandert niets. Daarna stap 15. | `abort(401)`. De collectiepagina zelf stuurt bezoekers naar `/login`. |
| 5 | De database start een schrijftransactie met `BEGIN IMMEDIATE`. | `film_action`; `with db`. Een tweede schrijfactie moet wachten. |
| 6 | Het systeem zoekt de DVD aan de hand van het ID. Verwijderde DVD's tellen niet mee. | `film_or_404`, SQL met `id=? AND deleted=0`. |
| 7 | Het systeem controleert of er een DVD is gevonden. | Controle op `film is None`. |
| 8 | Als de DVD ontbreekt volgt 404. De transactie wordt teruggedraaid. Daarna stap 15. | `abort(404)` en automatische rollback door `with db`. |
| 9 | Het systeem controleert of de status beschikbaar is. | Vergelijking `film['status'] != 'beschikbaar'`. |
| 10 | Bij uitgeleend of gereserveerd volgt 409. De transactie wordt teruggedraaid. Daarna stap 15. | `abort(409)`. Er komt geen logregel voor een mislukte reservering. |
| 11 | De status wordt gereserveerd en de huidige gebruiker wordt gekoppeld als eigenaar. | `UPDATE film SET status=?, holder_id=? WHERE id=?`. |
| 12 | Een logregel bewaart de actie reserveren, de DVD, de uitvoerende gebruiker en de UTC-tijd. | `INSERT INTO logging`; timestamp via database-default. |
| 13 | De wijzigingen en logregel worden samen definitief opgeslagen. | Commit bij succesvol verlaten van `with db`. |
| 14 | De API geeft de bijgewerkte DVD terug. De browser toont de bevestiging en vernieuwt de collectie. | JSON-antwoord en `loadFilms()` in JavaScript. |
| 15 | Het proces eindigt. | De klant kan een volgende handeling kiezen. |

## Afbakening en foutafhandeling

Het schema toont het reserveringsproces. Het algemene CSRF-filter controleert vooraf ook iedere POST-aanvraag. Een ongeldig token geeft 400 en bereikt dit proces niet. Bij een onverwachte databasefout rolt de contextmanager de transactie terug. De reserveringswijziging en de logregel kunnen daardoor niet half worden opgeslagen.

Een gereserveerde DVD mag niet worden geleend, ook niet door de reserveerder. Bij ophalen annuleert de klant of beheerder eerst de reservering. Daarna kan de DVD worden geleend. Beide stappen hebben een eigen logregel.
