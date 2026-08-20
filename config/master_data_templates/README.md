# Vorlagen für lokale Stammdaten

Diese Dateien definieren nur Struktur und Pflichtfelder. Echte Kundenkennungen,
Fehlertexte und andere interne Stammdaten gehören nach
`data/local/master_data/` und werden nicht mit Git versioniert.

## Dateien

- `accepted_negative_customers.csv`: fachlich freigegebene Auslastungskunden,
  bei denen ein negativer Auftragsertrag grundsätzlich zulässig ist.
- `error_categories.csv`: kontrollierte Werteliste für manuelle Prüfergebnisse.

Ein Eintrag ist nur wirksam, wenn die Kundennummer nicht leer ist und der
Gültigkeitszeitraum zum Auftragsdatum passt. Freigabeinformationen werden für die
spätere revisionsfähige Nutzung benötigt.

Im Feld `customer_key` darf entweder der vollständige Schlüssel aus dem Export
oder die Kundennummer nach dem Firmenschlüssel und dem Trenner `|` stehen.
