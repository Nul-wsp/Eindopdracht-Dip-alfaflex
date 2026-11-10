# Testresultaten AlfaFlix

Controle uitgevoerd op 9 november 2026 met Python 3.12, Flask 3.1.2 en een tijdelijke SQLite-database. Er zijn geen testaccounts of databases met gebruikersgegevens opgenomen in het opleverpakket.

## Automatische tests

Opdracht: `python -m pytest -q`

**Resultaat: 27 tests geslaagd.**

| Groep | Gecontroleerd |
|---|---|
| Accounts | Registratie, login, logout, wachtwoordhash, dubbele naam zonder hoofdletteronderscheid, onjuist wachtwoord, ongeldige registratie. |
| Toegang | Beschermde collectie, geschiedenis en beheer; 401 voor anonieme API-aanvragen; 403 voor gewone gebruiker bij beheer. |
| CSRF | Mutaties zonder of met verkeerd token geweigerd; logout werkt niet als GET. |
| Verhuur | Lenen, terugbrengen, dubbele verhuur blokkeren, retour met verkeerde status weigeren. |
| Reserveringen | Reserveren, blokkeren van lenen tijdens reservering, annuleren en daarna kunnen lenen. |
| Eigenaarschap | Andere klant kan niet retourneren/annuleren en ziet geen privélogs of holder-ID. Admin mag namens een klant handelen. |
| Logging | Juiste actie, uitvoerder en UTC-tijd; geen extra logregel bij geweigerde handeling. |
| CRUD | Toevoegen, lezen, bewerken, verwijderen; in gebruik zijnde DVD niet verwijderen; historie blijft bestaan. |
| Invoer | Lege/te lange titel, onjuist type, ongeldige getallen en onbekende velden geweigerd. |
| Zoeken | Zoeken op titel en filteren op status, onbekend ID/status en verkeerde JSON afgevangen. |
| Gelijktijdigheid | Twee gebruikers lenen tegelijk dezelfde DVD: één 200, één 409, één logregel. |
| Herstart | Geen dubbele seeddata en geen terugkeer van verwijderde DVD's na opnieuw initialiseren. |
| TMDB | Ontbrekend token, succesvolle omschrijving/poster, time-out, onvolledige gegevens en ontbrekend film-ID met mocks getest. |
| CLI | Admin aanmaken, dubbele naam weigeren, geen rolverhoging door registratievelden. |

## Browsercontrole

Met headless Chromium zijn de echte pagina's en JavaScript getest:

- Registreren en inloggen via de formulieren.
- Zes voorbeeldfilms laden via de API.
- Reserveren, blokkeren van Lenen, annuleren, lenen en terugbrengen.
- Gegevens aanpassen via de bewerkdialoog.
- DVD toevoegen en verwijderen via het beheerpaneel.
- Geschiedenis met de vier uitgevoerde handelingen.
- Swagger-documentatie laden met 12 gedocumenteerde operaties.
- Vanuit Swagger daadwerkelijk GET /api/films (200) en POST /api/films (201) uitvoeren, met automatisch CSRF-token.
- Collectie op desktop (1440px) en mobiel (390px), zonder horizontale overflow.
- Uitloggen via POST.
- Geen JavaScript-fouten in de afgeronde gebruikersflow.

Bootstrap en Swagger zijn lokaal opgenomen nadat de browsercontrole een probleem met externe stylesheets liet zien. De uiteindelijke weergave is visueel gecontroleerd.

`swagger.yaml` is ook met `openapi-spec-validator` gevalideerd als OpenAPI 3.0.3. Het SVG-stroomschema is geopend en visueel gecontroleerd.

## Nog zelf doen

- De app op jouw Windows-computer starten en een eigen beheerder aanmaken.
- Een eigen TMDB Read Access Token instellen en omschrijving/poster live ophalen. Er was geen gebruikers-token beschikbaar; de externe integratie is daarom met gecontroleerde simulaties getest.
- Naam/klas/studentnummer en repositorylink in assessment.md invullen.
- Private GitHub-repository aanmaken, docenten uitnodigen en link inleveren op ItsLearning.
