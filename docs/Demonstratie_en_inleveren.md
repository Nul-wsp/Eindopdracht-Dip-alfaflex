# Demonstratie en inleveren

## Eerst lokaal controleren

Werk met je eigen accounts en lees de technische uitleg zodat je de werking kunt toelichten. De onderstaande stappen kun je tijdens een demonstratie laten zien. Maak desgewenst zelf screenshots van de genoemde momenten; er zijn geen verzonnen screenshots of live TMDB-resultaten meegeleverd.

| Stap | Wat doe je? | Wat moet zichtbaar zijn? |
|---|---|---|
| 1 | Start de app, open `/videotheek` zonder login. | Je wordt naar Inloggen gestuurd. |
| 2 | Registreer bijvoorbeeld `klant1` en log in. | Je ziet de zes voorbeeldfilms met status beschikbaar. |
| 3 | Reserveer The Matrix. | Status gereserveerd; geen knop Lenen. |
| 4 | Annuleer en leen daarna dezelfde DVD. | Status uitgeleend; knop Terugbrengen. |
| 5 | Open een privévenster, registreer `klant2` en log in. | De DVD is ook hier uitgeleend; klant2 kan hem niet lenen of terugbrengen. |
| 6 | Ga in het eerste venster terug naar klant1 en klik Terugbrengen. | Status wordt beschikbaar. |
| 7 | Open Geschiedenis. | Reserveren, annuleren, huren en terugbrengen met naam en datum/tijd. |
| 8 | Maak via de CLI een admin en log daarmee in. | Link Beheer verschijnt. |
| 9 | Voeg een eigen DVD toe via Beheer. | De nieuwe DVD verschijnt. |
| 10 | Bewerk titel of genre via Collectie. | De gewijzigde gegevens blijven na vernieuwen bestaan. |
| 11 | Verwijder de eigen beschikbare DVD via Beheer. | De DVD verdwijnt uit de collectie. |
| 12 | Open `/api/docs`. Probeer GET, POST, PATCH en DELETE. | Swagger toont API-aanvragen en antwoorden; maak eventueel een aparte test-DVD. |
| 13 | Stel je TMDB-token in volgens README en herstart. Haal gegevens op voor een voorbeeldfilm. | Een echte poster en opgehaalde omschrijving. Dit moet je nog live met je eigen token controleren. |
| 14 | Open het stroomschema en de bijbehorende uitleg. | 15 stappen met Ja/Nee-takken. |
| 15 | Voer `python -m pytest -q` uit met de projectvenv. | Alle 27 tests slagen. |

Voor een eenvoudig bewijs kun je screenshots maken na stap 2, 3, 4, 7, 9, 12, 13 en 15. Gebruik geen zichtbaar wachtwoord of TMDB-token in screenshots.

## GitHub-repository en ItsLearning

Deze accountacties zijn niet voor je uitgevoerd. In de originele opdracht staat dat de repository private moet zijn en dat beide docenten toegang moeten krijgen.

1. Controleer `assessment.md`. Vul je naam, klas en studentnummer in.
2. Controleer de werking op jouw computer en voer de TMDB-controle uit als je keuze 2 wilt laten beoordelen.
3. Maak in jouw eigen GitHub-account een **nieuwe private repository**, bijvoorbeeld `DIP2-AlfaFlix`. Maak deze leeg aan, dus zonder extra README, license of gitignore.
4. Open een VS Code-terminal in de map waar `app.py` staat.
5. Voer uit:

```powershell
git init
git add .
git commit -m "AlfaFlix eindopdracht DiP2 uitgewerkt"
git branch -M main
git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/DIP2-AlfaFlix.git
git push -u origin main
```

Vervang `JOUW-GEBRUIKERSNAAM` door je eigen GitHub-naam. Meld je aan als GitHub daarom vraagt. Heeft de map al een origin? Controleer eerst `git remote -v` en pas die alleen aan als deze inderdaad naar jouw inleverrepository moet verwijzen.

6. Controleer op GitHub of `app.py`, `schema.sql`, `swagger.yaml`, `assessment.md`, `templates`, `static`, `docs` en `tests` zichtbaar zijn. `.env`, `instance` en `.venv` horen niet in GitHub te staan.
7. Open de repository-instellingen en de pagina voor medewerkers/collaborators. Nodig de twee docenten uit met de e-mailadressen uit de opdracht:
   - `hj.prins@alfa-college.nl`
   - `wg.weges@alfa-college.nl`
8. Kan GitHub een docent niet vinden via e-mail? Vraag de docent om de GitHub-gebruikersnaam. Kies geen willekeurig gelijkend account.
9. Vul de repositorylink in `assessment.md` in en commit/push deze aanpassing:

```powershell
git add assessment.md
git commit -m "Repositorylink toegevoegd aan assessment"
git push
```

10. Lever de repositorylink in op ItsLearning. Controleer of de docenten zijn uitgenodigd en je nieuwste commit zichtbaar is.

## Korte uitleg tijdens een beoordeling

- “Elke rij in film is één DVD-exemplaar. De status geeft aan of deze vrij is.”
- “De gebruiker logt in met een gehasht wachtwoord. Zijn ID staat in een ondertekende sessie.”
- “De site gebruikt dezelfde API als Swagger. Alleen de beheerder kan filmgegevens aanpassen of DVD's toevoegen/verwijderen.”
- “Een transactie bewaart de statuswijziging en de logregel samen.”
- “Bij reserveren controleer ik eerst de login, de DVD en de beschikbaarheid.”
- “De TMDB-token staat alleen op de server. Ik sla de opgehaalde omschrijving en poster-URL op.”
