# Stroomschema: een DVD reserveren

Open Stroomschema.svg in je browser. Het schema toont de API-reservering; de website gebruikt dezelfde functie verwerk_actie().

Afgerond vak = start/einde. Rechthoek = verwerking. Ruit = beslissing. Parallellogram = invoer/uitvoer. De pijlen geven de volgorde aan.

| Stap | Uitleg |
|---|---|
| 1 | De reservering begint. |
| 2 | De klant kiest een DVD en verstuurt een reserveringsaanvraag. |
| 3 | Het systeem controleert of de klant is ingelogd. |
| 4 | Zonder login geeft de API foutcode 401. Daarna eindigt het proces. De website stuurt een bezoeker naar de loginpagina. |
| 5 | Start een database-transactie. Andere wijzigingen moeten even wachten. |
| 6 | Zoek de DVD in de database. Verwijderde DVD's tellen niet mee. |
| 7 | Controleer of de DVD is gevonden. |
| 8 | Niet gevonden: geef 404 en draai de transactie terug. |
| 9 | Controleer of de status beschikbaar is. |
| 10 | Niet beschikbaar: geef 409 en draai de transactie terug. |
| 11 | Zet de status op gereserveerd en koppel het ingelogde gebruikers-ID. |
| 12 | Voeg een logregel toe met reserveren, DVD, gebruiker en tijd. |
| 13 | Sla de wijziging en de logregel samen op. |
| 14 | De API geeft de nieuwe status terug. Via de website wordt het overzicht opnieuw geladen met een melding. |
| 15 | Het proces is klaar. |

Het algemene formuliertoken wordt vóór dit proces gecontroleerd. Een verkeerd token geeft 400. Een mislukte reservering krijgt geen logregel. De statuswijziging en logregel staan in dezelfde transactie.
