# Datenkatalog SP_Naka

Dieser Katalog beschreibt Struktur, Bedeutung und Beziehungen der Datenquellen.
Er enthält ausschließlich Metadaten und synthetische Beispiele, keine echten
Geschäfts-, Personen- oder Zugangsdaten.

## Verwendung des Katalogs

1. Zuerst die Übersicht und die gemeinsamen Konventionen ausfüllen.
2. Danach jede Datenquelle in einem eigenen Abschnitt beschreiben.
3. Für jede Spalte den tatsächlichen Spaltennamen und die fachliche Bedeutung erfassen.
4. Vermutete Schlüssel oder Beziehungen ausdrücklich als `zu prüfen` kennzeichnen.
5. Nach einer Datenprüfung Status, Qualitätskennzahlen und Prüfdatum aktualisieren.
6. Änderungen an Struktur oder Bedeutung zusammen mit dem Programmcode versionieren.

Die Angaben `Logischer Tabellenname` und `Logischer Feldname` sollen später als
stabile Namen im Programm verwendet werden. Physische Datei- und Spaltennamen dürfen
sich ändern, ohne dass dadurch die fachliche Bedeutung verloren geht.

## Statuswerte

- `Entwurf`: Beschreibung ist noch unvollständig.
- `Zu prüfen`: Angabe wurde vermutet und muss anhand der Daten bestätigt werden.
- `Bestätigt`: Angabe wurde fachlich und technisch geprüft.
- `Veraltet`: Quelle oder Beschreibung wird nicht mehr verwendet.

## Übersicht der Datenquellen

| ID | Fachlicher Name | Logischer Tabellenname | Dateiname/Muster | Eine Zeile entspricht | Status | Verantwortlich | Letzte Prüfung |
|---|---|---|---|---|---|---|---|
| SRC-001 | Auftragskopf | `order_header` | _ausfüllen_ | genau einem Auftrag | Entwurf | _ausfüllen_ | _JJJJ-MM-TT_ |
| SRC-002 | Verkaufspositionen | `sales_order_item` | _ausfüllen_ | genau einer Verkaufsposition | Entwurf | _ausfüllen_ | _JJJJ-MM-TT_ |
| SRC-003 | Rohwarenpositionen | `raw_material_item` | _ausfüllen_ | _genau beschreiben_ | Entwurf | _ausfüllen_ | _JJJJ-MM-TT_ |
| SRC-004 | Rohwarenabgänge | `raw_material_issue` | _ausfüllen_ | genau einer Materialbewegung/Buchung | Entwurf | _ausfüllen_ | _JJJJ-MM-TT_ |
| SRC-005 | _weitere Datenquelle_ | `_logischer_name_` | _ausfüllen_ | _genau beschreiben_ | Entwurf | _ausfüllen_ | _JJJJ-MM-TT_ |

## Gemeinsame Konventionen

- **Zeichencodierung:** _z. B. UTF-8_
- **Spaltentrennzeichen:** _z. B. Semikolon_
- **Dezimaltrennzeichen:** _z. B. Komma_
- **Tausendertrennzeichen:** _ausfüllen_
- **Datumsformat:** _z. B. TT.MM.JJJJ_
- **Zeitformat/Zeitzone:** _ausfüllen_
- **Standardwährung:** _z. B. EUR; Abweichungen je Datensatz dokumentieren_
- **Mengeneinheiten:** _z. B. kg, t, Stück; Umrechnungen dokumentieren_
- **Darstellung fehlender Werte:** _z. B. leer, NULL, 0; Bedeutung unterscheiden_
- **Dateilieferung/Aktualisierung:** _z. B. täglich als Vollbestand_
- **Historisierung:** _Vollbestand, Änderungslieferung oder Stichtag_

---

## SRC-001 – Auftragskopf

### Tabellenbeschreibung

- **Logischer Tabellenname:** `order_header`
- **Physischer Dateiname/Muster:** _ausfüllen_
- **Dateiformat:** _CSV / XLSX / Datenbank / anderes_
- **Tabellenblatt:** _falls relevant_
- **Fachlicher Zweck:** _ausfüllen_
- **Eine Zeile entspricht:** genau einem Auftrag – _bestätigen oder korrigieren_
- **Erwarteter Primärschlüssel:** `_auftragsnummer_` – `zu prüfen`
- **Zeitraum der Daten:** _ausfüllen_
- **Ungefähre Zeilenanzahl:** _ausfüllen_
- **Aktualisierung:** _Rhythmus und Lieferart_
- **Quellsystem:** _allgemeine Bezeichnung, keine Zugangsdaten_
- **Verantwortlich:** _ausfüllen_
- **Vertraulichkeitsstufe:** _ausfüllen_
- **Personenbezogene Daten:** Ja / Nein / Unklar
- **Zulässige Verwendung:** _ausfüllen_
- **Aufbewahrung/Löschung:** _ausfüllen_
- **Status:** Entwurf
- **Letzte Prüfung:** _JJJJ-MM-TT_

### Felder

| Physischer Spaltenname | Logischer Feldname | Fachliche Bedeutung | Datentyp/Format | Pflichtfeld | Schlüsselrolle | Referenz | Einheit/Währung | Erlaubte Werte/Regel | Synthetisches Beispiel | Bemerkung |
|---|---|---|---|---|---|---|---|---|---|---|
| _ausfüllen_ | `order_id` | Eindeutige Auftragskennung | Text | Ja | PK-Kandidat | – | – | eindeutig, nicht leer | `ORD-10001` | zu prüfen |
| _ausfüllen_ | `order_date` | Auftragsdatum | Datum | _Ja/Nein_ | – | – | – | gültiges Datum | `2026-01-15` | |
| _ausfüllen_ | `_feldname_` | _Beschreibung_ | _Typ_ | _Ja/Nein_ | _PK/FK/–_ | _Tabelle.Feld_ | _Einheit_ | _Regel_ | _synthetisch_ | |

### Datenqualität

- **Eindeutigkeit des Primärschlüssels:** _ungeprüft / Ergebnis_
- **Fehlende Schlüsselwerte:** _ungeprüft / Anzahl oder Anteil_
- **Doppelte Aufträge:** _ungeprüft / Ergebnis_
- **Ungültige Datumswerte:** _ungeprüft / Ergebnis_
- **Bekannte fachliche Probleme:** _ausfüllen_
- **Geplante Prüfregeln:** _ausfüllen_

---

## SRC-002 – Verkaufspositionen

### Tabellenbeschreibung

- **Logischer Tabellenname:** `sales_order_item`
- **Physischer Dateiname/Muster:** _ausfüllen_
- **Dateiformat:** _CSV / XLSX / Datenbank / anderes_
- **Tabellenblatt:** _falls relevant_
- **Fachlicher Zweck:** _ausfüllen_
- **Eine Zeile entspricht:** genau einer Position eines Auftrags – _bestätigen oder korrigieren_
- **Erwarteter Primärschlüssel:** Kombination aus `_auftragsnummer_` und `_positionsnummer_` – `zu prüfen`
- **Erwarteter Fremdschlüssel:** `_auftragsnummer_` auf `order_header.order_id` – `zu prüfen`
- **Zeitraum der Daten:** _ausfüllen_
- **Ungefähre Zeilenanzahl:** _ausfüllen_
- **Aktualisierung:** _Rhythmus und Lieferart_
- **Quellsystem:** _allgemeine Bezeichnung, keine Zugangsdaten_
- **Verantwortlich:** _ausfüllen_
- **Vertraulichkeitsstufe:** _ausfüllen_
- **Personenbezogene Daten:** Ja / Nein / Unklar
- **Status:** Entwurf
- **Letzte Prüfung:** _JJJJ-MM-TT_

### Felder

| Physischer Spaltenname | Logischer Feldname | Fachliche Bedeutung | Datentyp/Format | Pflichtfeld | Schlüsselrolle | Referenz | Einheit/Währung | Erlaubte Werte/Regel | Synthetisches Beispiel | Bemerkung |
|---|---|---|---|---|---|---|---|---|---|---|
| _ausfüllen_ | `order_id` | Auftragskennung | Text | Ja | PK-Teil, FK | `order_header.order_id` | – | nicht leer | `ORD-10001` | zu prüfen |
| _ausfüllen_ | `sales_item_id` | Positionsnummer im Auftrag | Text/Ganzzahl | Ja | PK-Teil | – | – | je Auftrag eindeutig | `10` | zu prüfen |
| _ausfüllen_ | `sales_quantity` | Verkaufsmenge | Dezimalzahl | _Ja/Nein_ | – | – | _ausfüllen_ | größer/gleich 0? | `125.50` | Vorzeichenregel klären |
| _ausfüllen_ | `sales_unit_price` | Preis je definierter Einheit | Dezimalzahl | _Ja/Nein_ | – | – | _Währung je Einheit_ | größer/gleich 0? | `18.90` | Preisbasis klären |
| _ausfüllen_ | `delivery_status` | Lieferstatus der Position | Text | _Ja/Nein_ | – | – | – | Werteliste ergänzen | `TEILGELIEFERT` | |
| _ausfüllen_ | `_feldname_` | _Beschreibung_ | _Typ_ | _Ja/Nein_ | _PK/FK/–_ | _Tabelle.Feld_ | _Einheit_ | _Regel_ | _synthetisch_ | |

### Datenqualität

- **Eindeutigkeit Auftrag + Position:** _ungeprüft / Ergebnis_
- **Positionen ohne passenden Auftragskopf:** _ungeprüft / Anzahl oder Anteil_
- **Fehlende oder negative Mengen:** _ungeprüft / Ergebnis_
- **Fehlende oder negative Preise:** _ungeprüft / Ergebnis_
- **Unbekannte Lieferstatuswerte:** _ungeprüft / Ergebnis_
- **Bekannte fachliche Probleme:** _ausfüllen_

---

## SRC-003 – Rohwarenpositionen

### Tabellenbeschreibung

- **Logischer Tabellenname:** `raw_material_item`
- **Physischer Dateiname/Muster:** _ausfüllen_
- **Dateiformat:** _CSV / XLSX / Datenbank / anderes_
- **Tabellenblatt:** _falls relevant_
- **Fachlicher Zweck:** _z. B. geplanter oder kalkulierter Rohwareneinsatz_
- **Eine Zeile entspricht:** _z. B. einer Rohware je Verkaufsposition; genau bestätigen_
- **Erwarteter Primärschlüssel:** _ausfüllen oder als nicht vorhanden kennzeichnen_
- **Mögliche Fremdschlüssel:** Auftrag, Verkaufsposition, Material – jeweils `zu prüfen`
- **Zeitraum der Daten:** _ausfüllen_
- **Ungefähre Zeilenanzahl:** _ausfüllen_
- **Aktualisierung:** _Rhythmus und Lieferart_
- **Quellsystem:** _allgemeine Bezeichnung, keine Zugangsdaten_
- **Verantwortlich:** _ausfüllen_
- **Vertraulichkeitsstufe:** _ausfüllen_
- **Personenbezogene Daten:** Ja / Nein / Unklar
- **Status:** Entwurf
- **Letzte Prüfung:** _JJJJ-MM-TT_

### Felder

| Physischer Spaltenname | Logischer Feldname | Fachliche Bedeutung | Datentyp/Format | Pflichtfeld | Schlüsselrolle | Referenz | Einheit/Währung | Erlaubte Werte/Regel | Synthetisches Beispiel | Bemerkung |
|---|---|---|---|---|---|---|---|---|---|---|
| _ausfüllen_ | `raw_material_item_id` | Eindeutige Rohwarenposition, falls vorhanden | Text | _Ja/Nein_ | PK-Kandidat | – | – | eindeutig, falls befüllt | `RM-50001` | zu prüfen |
| _ausfüllen_ | `order_id` | Mögliche Auftragskennung | Text | _Ja/Nein_ | FK-Kandidat | `order_header.order_id` | – | – | `ORD-10001` | Zuverlässigkeit klären |
| _ausfüllen_ | `sales_item_id` | Mögliche Verkaufspositionsnummer | Text/Ganzzahl | _Ja/Nein_ | FK-Kandidat | `sales_order_item.sales_item_id` | – | – | `10` | Nur mit order_id verwenden |
| _ausfüllen_ | `material_id` | Rohwaren-/Materialkennung | Text | _Ja/Nein_ | Schlüsselteil? | _Materialstamm, falls vorhanden_ | – | – | `MAT-2001` | |
| _ausfüllen_ | `planned_quantity` | Geplante Rohwarenmenge | Dezimalzahl | _Ja/Nein_ | – | – | _ausfüllen_ | Vorzeichenregel klären | `75.00` | |
| _ausfüllen_ | `_feldname_` | _Beschreibung_ | _Typ_ | _Ja/Nein_ | _PK/FK/–_ | _Tabelle.Feld_ | _Einheit_ | _Regel_ | _synthetisch_ | |

### Datenqualität

- **Eindeutigkeit des angenommenen Schlüssels:** _ungeprüft / Ergebnis_
- **Positionen ohne Auftrag:** _ungeprüft / Anzahl oder Anteil_
- **Positionen ohne passende Verkaufsposition:** _ungeprüft / Anzahl oder Anteil_
- **Fehlende Materialnummern:** _ungeprüft / Ergebnis_
- **Fehlende oder negative Mengen:** _ungeprüft / Ergebnis_
- **Bekannte fachliche Probleme:** _ausfüllen_

---

## SRC-004 – Rohwarenabgänge

### Tabellenbeschreibung

- **Logischer Tabellenname:** `raw_material_issue`
- **Physischer Dateiname/Muster:** _ausfüllen_
- **Dateiformat:** _CSV / XLSX / Datenbank / anderes_
- **Tabellenblatt:** _falls relevant_
- **Fachlicher Zweck:** _z. B. tatsächliche detaillierte Rohwarenentnahmen_
- **Eine Zeile entspricht:** genau einer Materialbewegung/Buchung – _bestätigen oder korrigieren_
- **Erwarteter Primärschlüssel:** `_buchungsnummer_` – `zu prüfen`
- **Mögliche Fremdschlüssel:** Auftrag, Verkaufsposition, Rohwarenposition, Material – jeweils `zu prüfen`
- **Zeitraum der Daten:** _ausfüllen_
- **Ungefähre Zeilenanzahl:** _ausfüllen_
- **Aktualisierung:** _Rhythmus und Lieferart_
- **Quellsystem:** _allgemeine Bezeichnung, keine Zugangsdaten_
- **Verantwortlich:** _ausfüllen_
- **Vertraulichkeitsstufe:** _ausfüllen_
- **Personenbezogene Daten:** Ja / Nein / Unklar
- **Status:** Entwurf
- **Letzte Prüfung:** _JJJJ-MM-TT_

### Felder

| Physischer Spaltenname | Logischer Feldname | Fachliche Bedeutung | Datentyp/Format | Pflichtfeld | Schlüsselrolle | Referenz | Einheit/Währung | Erlaubte Werte/Regel | Synthetisches Beispiel | Bemerkung |
|---|---|---|---|---|---|---|---|---|---|---|
| _ausfüllen_ | `material_issue_id` | Eindeutige Buchungskennung | Text | Ja | PK-Kandidat | – | – | eindeutig, nicht leer | `ISS-90001` | zu prüfen |
| _ausfüllen_ | `booking_date` | Buchungsdatum/-zeit | Datum/Zeit | _Ja/Nein_ | – | – | – | gültiger Zeitpunkt | `2026-01-17 08:30` | Zeitzone klären |
| _ausfüllen_ | `material_id` | Rohwaren-/Materialkennung | Text | _Ja/Nein_ | FK-Kandidat | _Materialstamm, falls vorhanden_ | – | – | `MAT-2001` | |
| _ausfüllen_ | `issued_quantity` | Tatsächlich gebuchte Menge | Dezimalzahl | _Ja/Nein_ | – | – | _ausfüllen_ | Vorzeichenregel klären | `25.00` | Storno separat klären |
| _ausfüllen_ | `order_id` | Angegebene oder abgeleitete Auftragskennung | Text | _Ja/Nein_ | FK-Kandidat | `order_header.order_id` | – | – | `ORD-10001` | Herkunft kennzeichnen |
| _ausfüllen_ | `sales_item_id` | Angegebene oder abgeleitete Verkaufsposition | Text/Ganzzahl | _Ja/Nein_ | FK-Kandidat | `sales_order_item.sales_item_id` | – | – | `10` | Nur mit order_id eindeutig |
| _ausfüllen_ | `_feldname_` | _Beschreibung_ | _Typ_ | _Ja/Nein_ | _PK/FK/–_ | _Tabelle.Feld_ | _Einheit_ | _Regel_ | _synthetisch_ | |

### Datenqualität

- **Eindeutigkeit der Buchungskennung:** _ungeprüft / Ergebnis_
- **Buchungen ohne Materialnummer:** _ungeprüft / Anzahl oder Anteil_
- **Buchungen ohne mögliche Auftragszuordnung:** _ungeprüft / Anzahl oder Anteil_
- **Mehrdeutige Zuordnungen:** _ungeprüft / Anzahl oder Anteil_
- **Storno- und Korrekturbuchungen:** _Regel beschreiben_
- **Unbekannte oder wechselnde Einheiten:** _ungeprüft / Ergebnis_
- **Bekannte fachliche Probleme:** _ausfüllen_

---

## Beziehungen zwischen den Tabellen

Keine Beziehung als sicher voraussetzen, bevor Schlüssel und Kardinalität anhand
der Daten geprüft wurden.

| Von Tabelle/Feld | Zu Tabelle/Feld | Erwartete Kardinalität | Pflichtbeziehung | Zuordnungsmethode | Status | Verwaiste Datensätze | Bemerkung |
|---|---|---|---|---|---|---|---|
| `sales_order_item.order_id` | `order_header.order_id` | n:1 | _Ja/Nein_ | exakter Schlüssel | Zu prüfen | _ungeprüft_ | |
| `raw_material_item.order_id` | `order_header.order_id` | n:1 | _Ja/Nein_ | exakter Schlüssel? | Zu prüfen | _ungeprüft_ | |
| `raw_material_item.(order_id, sales_item_id)` | `sales_order_item.(order_id, sales_item_id)` | n:1 oder n:m? | _Ja/Nein_ | zusammengesetzter Schlüssel? | Zu prüfen | _ungeprüft_ | |
| `raw_material_issue.order_id` | `order_header.order_id` | n:1 oder optional | Nein | direkt oder abgeleitet? | Zu prüfen | _ungeprüft_ | |
| `raw_material_issue` | `raw_material_item` | n:1, n:m oder keine | Nein | fachliche Zuordnung | Zu prüfen | _ungeprüft_ | Nicht künstlich erzwingen |
| _weitere Beziehung_ | _Zieltabelle/Feld_ | _1:1 / 1:n / n:m_ | _Ja/Nein_ | _Methode_ | Entwurf | _ungeprüft_ | |

## Regeln für optionale Zuordnungen

Rohwarenabgänge können zu einer Rohwaren- oder Verkaufsposition passen, müssen es
aber nicht. Eine spätere automatische Zuordnung soll deshalb getrennt von den
Originaldaten gespeichert werden und mindestens folgende Angaben enthalten:

| Feld | Bedeutung | Beispiel |
|---|---|---|
| `material_issue_id` | Zu prüfende Rohwarenbuchung | `ISS-90001` |
| `candidate_order_id` | Möglicher Auftrag | `ORD-10001` |
| `candidate_sales_item_id` | Mögliche Verkaufsposition | `10` |
| `candidate_raw_material_item_id` | Mögliche Rohwarenposition | `RM-50001` |
| `assignment_status` | `eindeutig`, `wahrscheinlich`, `mehrdeutig`, `nicht_zugeordnet`, `manuell_bestaetigt` | `wahrscheinlich` |
| `confidence` | Nachvollziehbarer Wert von 0 bis 1 | `0.85` |
| `assignment_method` | Verwendete Regel oder Modellversion | `material_menge_datum_v1` |
| `assignment_reason` | Verständliche Begründung ohne vertrauliche Daten | `Material und Zeitraum stimmen überein` |
| `reviewed_by` | Fachliche Prüfung, falls vorhanden | `Rolle/Team` |
| `reviewed_at` | Prüfdatum | `2026-02-01` |

Mehrdeutige Beziehungen dürfen nicht durch einen normalen Join aufgelöst werden,
weil dies Mengen und Werte vervielfachen kann. Für n:m-Beziehungen ist eine eigene
Zuordnungs- oder Brückentabelle erforderlich.

## Übergreifende Qualitätsprüfungen

| Prüfung | Erwartung | Ergebnis | Status | Letzte Prüfung |
|---|---|---|---|---|
| Primärschlüssel sind eindeutig | Keine Duplikate je definiertem Schlüssel | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Pflichtschlüssel sind befüllt | Keine leeren Pflichtschlüssel | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Verkaufspositionen haben Auftragsköpfe | Anteil und Ausnahmen dokumentiert | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Einheiten sind eindeutig interpretierbar | Einheit je Mengenfeld bekannt | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Währungen und Preisbasen sind bekannt | Keine Vermischung ohne Umrechnung | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Zeiträume der Quellen sind kompatibel | Abweichungen dokumentiert | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Stornos/Korrekturen sind erkennbar | Verarbeitungsregel dokumentiert | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |
| Nicht zuordenbare Abgänge bleiben sichtbar | Keine stillschweigende Entfernung | _ungeprüft_ | Entwurf | _JJJJ-MM-TT_ |

## Freigabe und Änderungsverlauf

- **Fachlich geprüft durch:** _ausfüllen_
- **Technisch geprüft durch:** _ausfüllen_
- **Freigabestatus:** Entwurf
- **Gültig ab:** _JJJJ-MM-TT_
- **Nächste Überprüfung:** _JJJJ-MM-TT_
- **Offene Fragen:** _ausfüllen_

Bei Strukturänderungen an einer Quelldatei werden die betroffenen Tabellen- und
Feldbeschreibungen aktualisiert. Wesentliche Änderungen werden zusätzlich in
`docs/CHANGELOG.md` dokumentiert.
