# Datenkatalog SP_Naka

Dieser Katalog beschreibt die lokal bereitgestellten Datenquellen anhand einer
strukturellen Prüfung vom 2026-08-12. Er enthält keine echten Datensätze oder
Geschäftswerte, sondern nur Metadaten und aggregierte Qualitätskennzahlen.

## Statuskennzeichnung

- **Bestätigt:** technisch anhand des vollständigen CSV-Bestands geprüft.
- **Plausibel:** aus Name und Struktur abgeleitet, fachlich noch zu bestätigen.
- **OFFEN:** muss fachlich oder durch das Quellsystem definiert werden.

## Grenzen der Prüfung

- Geprüft wurden Struktur, Datentypmuster, Vollständigkeit, Eindeutigkeit und
  naheliegende Schlüsselbeziehungen.
- Feldbedeutungen wurden nicht als Tatsache angenommen, wenn sie nicht aus der
  Struktur eindeutig hervorgehen.
- Negative Werte, Nullwerte und Statuscodes wurden gezählt, aber nicht fachlich
  bewertet.
- Die frühere Datei `MegenMeldung.csv` ist im aktuellen Export nicht mehr enthalten
  und wurde daher aus dem aktiven Katalog entfernt.
- Verantwortlichkeit, Aktualisierungsrhythmus, Aufbewahrung und Freigabestatus
  können nicht aus den Dateien abgeleitet werden.

## Technische Beurteilung der CSV-Dateien

Alle zehn Dateien sind technisch lesbar und grundsätzlich für eine automatisierte
Verarbeitung geeignet.

| Eigenschaft | Ergebnis | Bewertung |
|---|---|---|
| Kodierung | UTF-8 mit BOM | Bestätigt; gut für Umlaute und Excel |
| Trennzeichen | Komma | Bestätigt |
| Textbegrenzung | doppelte Anführungszeichen | Bestätigt |
| Dezimaldarstellung | überwiegend Dezimalkomma | Bestätigt; Parser muss `decimal=","` berücksichtigen |
| Zeilenende | CRLF | Bestätigt; plattformübergreifend lesbar |
| Beschädigte/ungleich lange Zeilen | 0 | Bestätigt |
| Leere Datenzeilen | 0 | Bestätigt |
| Leere oder doppelte Header | 0 | Bestätigt |

Für alle zehn Quellen liegt außerdem eine gleichnamige Datei im lokalen
Testdatenverzeichnis vor. Die Header stimmen jeweils exakt mit der zugehörigen
Originaldatei überein. Die fachliche Abdeckung von Grenz- und Fehlerfällen durch
diese kleinen Testausschnitte ist noch nicht bestätigt.

### Technische Importregeln

- CSV-Dateien immer explizit als UTF-8 mit BOM, Komma-Trennzeichen und
  Anführungszeichen einlesen.
- Dezimalkomma in Mengen- und Wertfeldern explizit konfigurieren.
- Schlüssel und Artikelnummern als Text einlesen, auch wenn sie nur aus Ziffern
  bestehen; führende Nullen müssen erhalten bleiben.
- Physische Header mit Leerzeichen, Umlauten und unterschiedlicher Schreibweise
  über eine dokumentierte Mapping-Schicht auf stabile logische Namen abbilden.
- Quelldateien ausschließlich lesend öffnen und niemals normalisieren oder
  überschreiben. Bereinigte Daten gehören in eine getrennte Staging-Schicht.
- Für alle Tabellen mit Artikeln soll der Export zukünftig einen stabilen
  Artikelgruppenschlüssel und eine Gruppenbezeichnung enthalten. Bis dahin sind
  Materialfaktoren, die Gruppen wie Papier/Karton abgrenzen, nur teilweise
  vollständig.

## Übergreifende offene Angaben

- **Bestätigt:** Der Export umfasst drei Jahre rückwirkend. **OFFEN:** Handelt es
  sich dabei je Datei um einen Vollbestand, einen Stichtag oder eine Änderungslieferung?
- **Bestätigt:** Die Daten werden einmal pro Woche aktualisiert. **OFFEN:** Woran
  ist erkennbar, dass ein Export vollständig abgeschlossen ist?
- **Bestätigt:** Für Datums- und Zeitfelder gilt mitteleuropäische Zeit.
  **OFFEN:** Wie werden Sommerzeit und Zeitangaben ohne Uhrzeit behandelt?
- **Bestätigt:** Felder ohne Währungsangabe werden in EUR geführt.
- **OFFEN:** Welche Mengeneinheiten und Umrechnungsregeln gelten je Tabelle?
- **OFFEN:** Bedeutet leer immer „nicht vorhanden“, oder teilweise „unbekannt“?
- **OFFEN:** Welche Vertraulichkeitsstufe, Aufbewahrungsfrist und Löschregel gilt?
- **OFFEN:** Welche Status- und Codewertelisten existieren im Quellsystem?

## Übersicht der Datenquellen

| ID | Datei | Logischer Tabellenname | Zeilen | Spalten | Technisch beobachtetes Tabellenkorn | Schlüsselstatus |
|---|---|---|---:|---:|---|---|
| SRC-001 | `Auftragskopf.csv` | `order_header` | 38.884 | 20 | eine eindeutige Auftragskopfzeile | drei eindeutige Kennungen bestätigt |
| SRC-002 | `VertriebsPositionen.csv` | `sales_order_item` | 102.958 | 18 | eine eindeutige Vertriebsposition | Einzel- und zusammengesetzter Schlüssel bestätigt |
| SRC-003 | `RohwarenPos.csv` | `raw_material_item` | 42.814 | 18 | eine eindeutige Rohwaren-/Belegposition | mehrere eindeutige Kennungen bestätigt |
| SRC-004 | `RW_Buchungen.csv` | `raw_material_booking` | 65.805 | 9 | vermutlich eine Rohwarenbuchung | kein fachlich freigegebener Einzelbelegschlüssel |
| SRC-005 | `Fertigungsmaterial.csv` | `production_material_usage` | 151.837 | 8 | vermutlich ein Materialverbrauch je Auftrag/Artikel/Gruppe | Kandidat nicht eindeutig |
| SRC-006 | `ProdZeiten.csv` | `production_time_entry` | 398.869 | 17 | vermutlich eine Produktionszeit-/Arbeitsgangmeldung | keine Ereignis-ID vorhanden |
| SRC-007 | `Planung.csv` | `production_plan_entry` | 264.707 | 17 | ein Planungsdatensatz je technischer `Id` | `Id` eindeutig bestätigt |
| SRC-008 | `KTRBuchungenKI.csv` | `cost_object_booking` | 13.827 | 8 | summierte Kostenträgerbuchungen bestimmter Kostenarten | keine Buchungs-ID vorhanden |
| SRC-009 | `Rechnungskontrollen.csv` | `invoice_control_item` | 9.499 | 11 | Rechnungskontrollpositionen für auftragsbezogene Beschaffungen | kein eindeutiger Schlüssel bestätigt |
| SRC-010 | `Faktura.csv` | `order_billing_summary` | 27.334 | 11 | eine Faktura-Zusammenfassung je Auftrag | beide Auftragskennungen eindeutig |

### Änderungen gegenüber der Prüfung vom 2026-08-10

- Neu: `Planung.csv` und `Faktura.csv`.
- Entfernt: `MegenMeldung.csv`.
- In `RohwarenPos.csv` entfallen die früheren Felder `Firma`, `Komm Key`,
  `VertriebAuftrag_Pos`, `WertPosition`, `Zusatzkostentyp` und `Gesamtgewicht`.
- In `RW_Buchungen.csv`, `Rechnungskontrollen.csv` und
  `VertriebsPositionen.csv` entfällt jeweils `Firma`.
- Zeilenzahlen, Zeiträume, Leerquoten und Beziehungsabdeckungen wurden vollständig
  auf Basis des Exports vom 2026-08-12 neu berechnet.

---

## SRC-001 – Auftragskopf

### Tabellenbeschreibung

- **Datei:** `Auftragskopf.csv`
- **Logischer Tabellenname:** `order_header`
- **Zeitraum:** 2023-01-01 bis 2026-08-11
- **Zeilen:** 38.884
- **Eine Zeile entspricht:** technisch einer eindeutigen Kopfzeile;
- **Eindeutige Schlüssel:** `BelegKopfKey`, `V_BelegKopf_Obj` und `BelegNummer`
- **Bevorzugter logischer Schlüssel:** `BelegKopfKey` als `order_header_key`;
  **OFFEN:** fachlich bestätigen, welcher Schlüssel systemübergreifend stabil ist.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `BelegDatum` | `order_date` | Datum, 100 % befüllt | Belegdatum des Auftrages/Bestelldatum des Kunden. Relevantes Datum für Auswertungen |
| `V_BelegKopf_Obj` | `order_header_object_id` | Text, eindeutig, vollständig | technischer Schlüssel; Ist eindeutisger Schlüssel, wird aber aktuell nicht in anderen Tabellen verwendet |
| `BelegKopfKey` | `order_header_key` | Text, eindeutig, vollständig | Primärschlüssel |
| `Kunde Key` | `customer_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Kundenstamm  |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Boolean- Auftrag archiviert und Abgeschlossen oder eben noch Offen |
| `BelegNummer` | `order_number` | ziffernartige ID, eindeutig | fachliche Auftragsnummer; als Text importieren |
| `Zusatztext` | `additional_text` | Text, vollständig | Freitext; Auftrags/Projektbeschreibung |
| `X_ArtikelGruppe` | `article_group_code` | gemischte ID, 4,359 % leer | als Text importieren; Artikelgruppe- Welche Produktkategorie soll Produziert werden |
| `ArtikelGruppeBez` | `article_group_name` | Text, vollständig | Bezeichnung; 37 Ausprägungen beobachtet Artikelgruppe- Welche Produktkategorie soll Produziert werden |
| `Erlöse` | `revenue_amount` | Dezimalzahl, vollständig | Berechnete Erlöse des Autrags in EUR; Tatsächliche erlöse + Erlöse die aufgrund des Bestands zu erwarten sind. Mögliche Gutschriften/Bonus sind inkludiert |
| `Kosten` | `cost_amount` | Dezimalzahl, vollständig | Summe der osten lt. Nachkalkulation in EUR 5 negative Werte |
| `Produktionsstatus` | `production_status` | Text, 2 Ausprägungen | Sollten nur Fertige oder Stornierte Aufträge sein- sind in der Produktion abgeschlossen, Diverse Leistungen können zukünftig noch anfallen, Versand, Lagerhaltung,.. |
| `AuftragStatus` | `order_status_code` | Ganzzahl, 2 Ausprägungen | Werteliste und Abgrenzung zu `Status` offen |
| `NakaOK` | `naka_ok_code` | Ganzzahl, 2 Ausprägungen | fachliche Prüflogik offen |
| `NakaBem` | `naka_comment` | Text, 99,995 % leer | nur 2 befüllte Zeilen; Notwendigkeit und Vertraulichkeit prüfen |
| `AuftragsArt` | `order_type` | Text, 5 Ausprägungen | Werteliste offen |
| `MargenTage` | `margin_days` | Zahl, vollständig | überwiegend ganzzahlig, 10 Dezimalwerte; Berechnung/Rundung offen |
| `Vertreter Key` | `sales_representative_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Vertreterstamm vermutet |
| `Status` | `status_text` | Text, 2 Ausprägungen | Abgrenzung zu Auftrag-/Produktionsstatus offen |
| `GesamtNettoEUR` | `total_net_eur` | Dezimalzahl, vollständig | EUR laut Name; 1 negativer und 12.587 Nullwerte fachlich prüfen |

### Qualitätsbefund

- Alle drei Schlüssel sind vollständig und einzeln eindeutig.
- Negative Werte und Nullwerte dürfen nicht pauschal als Fehler behandelt werden;
  **OFFEN:** Gutschrift-, Storno- und unvollständige Aufträge definieren.
- Die drei Statusfelder dürfen nicht ohne fachliche Wertelisten zusammengeführt werden.

---

## SRC-002 – Vertriebspositionen

### Tabellenbeschreibung

- **Datei:** `VertriebsPositionen.csv`
- **Logischer Tabellenname:** `sales_order_item`
- **Zeilen:** 102.958
- **Eine Zeile entspricht:** technisch einer eindeutigen Vertriebsposition;
  fachliche Bestätigung steht aus.
- **Eindeutige Schlüssel:** `V_BelegPos_Obj` sowie
  (`BelegKopfKey`, `PositionsNr`)
- **Beziehung zum Auftragskopf:** 100 % über `BelegKopfKey`.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Artikel Key` | `article_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Artikelstamm vermutet |
| `BelegKopfKey` | `order_header_key` | Text, vollständig | FK zu `order_header`; nicht vollständig referenziell gedeckt |
| `PositionsNr` | `sales_item_number` | numerisch, vollständig | Teil des eindeutigen zusammengesetzten Schlüssels; 4 Dezimaldarstellungen prüfen |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Boolean- Position archiviert und Abgeschlossen oder eben noch Offen |
| `WertPosition` | `is_value_item_code` | Ganzzahl, 2 Ausprägungen | BWertposition wird direkt vererchnet, keine Bestände/LS |
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren; führende Nullen erhalten |
| `Menge` | `ordered_quantity` | Dezimalzahl, vollständig | Bedarfsmenge in Stk |
| `gelieferte_Menge` | `delivered_quantity` | Dezimalzahl, vollständig | Menge die bereits geliefert wurde |
| `Einzelpreis` | `unit_price` | Dezimalzahl, vollständig | Einzelpreis  |
| `EinzelpreismZuAbschl` | `unit_price_after_adjustment` | Dezimalzahl, vollständig | Mgliche zu und abschläge sind berücksichtigt |
| `Zusatzkostentyp` | `additional_cost_type_code` | Ganzzahl, 4 Ausprägungen | Werteliste offen |
| `KommissionsNr` | `commission_number` | ID, 12,999 % leer | KommissionsNr meist Auftragsnummer- wenn kein Wert kann Artikel von anderen Aufträgen entnommen werden |
| `Preiseinheitsfaktor` | `price_unit_factor` | positive Ganzzahl, vollständig | Einheit und Anwendung in Preisformeln; Meist per 1000 oder Per 1 |
| `KundenArtikelNr` | `customer_article_number` | gemischte ID, 7,782 % leer | als Text importieren; Fremdschlüssel/Verwendung offen |
| `GesamtNetto` | `total_net_amount` | Dezimalzahl, vollständig | **OFFEN:** Währung und Berechnung; 2 negative Werte |
| `Stornierte_Menge` | `cancelled_quantity` | Dezimalzahl, vollständig | Vorzeichenlogik offen; 86 negative Werte |
| `V_BelegPos_Obj` | `sales_item_object_id` | Text, eindeutig, vollständig | stabiler Einzel-Schlüsselkandidat |
| `Muster` | `construction_code` | Text, vollständig | Konstruktionsnummer; Werte mit Präfix `WM` werden für Peer-Gruppen verwendet, wenn keine eindeutige Stanzform vorliegt |

### Qualitätsbefund

- Positionsschlüssel sind technisch sehr gut geeignet.
- Die frühere Lücke zum Auftragskopf ist im aktuellen Export nicht mehr vorhanden.
- Numerisch wirkende Positions- und Artikelnummern dürfen nicht automatisch in
  Zahlen umgewandelt werden.

---

## SRC-003 – Rohwarenpositionen

### Tabellenbeschreibung

- **Datei:** `RohwarenPos.csv`
- **Logischer Tabellenname:** `raw_material_item`
- **Zeitraum Anlage:** 2023-01-02 bis 2026-08-05
- **Zeitraum Änderung:** 2023-01-09 bis 2026-08-12
- **Zeilen:** 42.814
- **Eine Zeile entspricht:** technisch einer eindeutigen Belegposition; dies sind die Bedarfsmengen der jeweiligen Rohware. Kann jedoch abweichen
- **Eindeutige Schlüssel:** `BelegposKey`, `BelegposBelegArtKey`,
  `V_BelegPos_Obj` sowie
  (`BelegKopf Key`, `PositionsNr`)
- **Beziehung zum Auftragskopf:** 100 % über `BelegKopf Key` und ebenso über
  `BelegNummer`.
- Keine Beziehung zu Vertriebspositionen nur zum Kopf
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Artikel Key` | `article_key` | Text, vollständig | Fremdschlüssel zu Artikelstamm  |
| `BelegKopf Key` | `order_header_key` | Text, vollständig | FK zum Auftragskopf; 100 % Treffer |
| `BelegposKey` | `document_item_key` | Text, eindeutig | bevorzugter lokaler Primärschlüsselkandidat |
| `BelegposBelegArtKey` | `document_item_type_key` | Text, eindeutig | Abgrenzung zu `BelegposKey` offen |
| `PositionsNr` | `raw_material_item_number` | numerisch, vollständig | 2 Dezimaldarstellungen; größer gleich 900 immer RW-Pos |
| `BelegArt` | `document_type` | Text, konstant | Bedeutung/Filterwirkung offen |
| `ReferenzNr` | `reference_number` | ziffernartige ID, vollständig | Referenz auf Auftragsebene; nicht eindeutig über Positionen |
| `BelegNummer` | `order_number` | ziffernartige ID, vollständig | gleiche Abdeckung zum Auftragskopf wie Kopf-Key |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Boolean- Position archiviert und Abgeschlossen oder eben noch Offen  |
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren |
| `Menge` | `ordered_quantity` | Dezimalzahl, vollständig | Einheit über Codefeld; 130 Nullwerte |
| `gelieferte_Menge` | `delivered_quantity` | Dezimalzahl, vollständig | 1 negativer Wert; menge die Abgebucht wurde- ist aber in SRC-004 detalierter |
| `reservierte_Menge` | `reserved_quantity` | Dezimalzahl, vollständig, immer 0 | derzeit ohne Informationsgehalt; Exportdefinition prüfen |
| `MengenEinheit` | `quantity_unit_code` | Ganzzahlcode, 4 Ausprägungen | zwingend Werteliste/Umrechnung bereitstellen |
| `Stornierte_Menge` | `cancelled_quantity` | Dezimalzahl, vollständig | 541 negative Werte; Vorzeichenregel offen |
| `AenderungDatum` | `modified_date` | Datum, vollständig | Zeitanteil/Zeitzone offen |
| `AnlageDatum` | `created_date` | Datum, vollständig | Zeitanteil/Zeitzone offen |
| `V_BelegPos_Obj` | `raw_material_item_object_id` | Text, eindeutig | technischer Schlüsselkandidat; nicht mit Vertriebsobjekt gleichsetzen |

### Qualitätsbefund

- Die Datei ist positionsintern gut schlüsselbar, Keine Verbindung zur
  Vertriebsposition.
- `reservierte_Menge` enthält ausschließlich Nullwerte.
- Verbindung zu Belekgopf bzw Rohwarenbuchungen, wobei Rohwarenbuchungen nicht zwingend eine Entsprechung in der Rohwarenpositionen finden muss

---

## SRC-004 – Rohwarenbuchungen

### Tabellenbeschreibung

- **Datei:** `RW_Buchungen.csv`
- **Logischer Tabellenname:** `raw_material_booking`
- **Zeitraum:** 2023-01-05 bis 2026-12-23
- **Zeilen:** 65.805
- **Eine Zeile entspricht:** plausibel einer Materialbuchung;
  fachlich bestätigen.
- **Schlüssel:** keine Buchungs-ID vorhanden. Die Snapshot-Kombination
  (`BelegNummer`, `BuchungsDatum`, `Artikel Key`, `Menge`, `WertMat`) ist eindeutig,
  aber nicht als dauerhafter Primärschlüssel freigegeben.
- **Beziehung zum Auftragskopf:** 100 % über `BelegNummer`.
- **Beziehung zu Rohwarenpositionen:** 98,473 % der Buchungszeilen beziehungsweise
  99,656 % der verschiedenen Belegnummern kommen in `RohwarenPos.csv` vor.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren |
| `Artikel Key` | `article_key` | Text, vollständig | Artikel-Fremdschlüsselkandidat |
| `S_Artikel_Obj` | `article_object_id` | Text, vollständig | Abgrenzung zu `Artikel Key` offen |
| `BelegNummer` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `BuchungsDatum` | `booking_date` | Datum, vollständig | ein Datum liegt nach dem aktuellen Analysestichtag; fachlich prüfen - Datum kann eingegeben werden- Fehler durch Mensch- wird normalerweise nicht korrigiert  |
| `Menge` | `booked_quantity` | Dezimalzahl, vollständig | 55.260 negativ, 10.423 positiv; Vorzeichenlogik zwingend definieren |
| `WertMat` | `material_value` | Dezimalzahl, vollständig | 53.979 negativ; immer in EUR |
| `MengeKG` | `quantity_kg` | 100 % leer | derzeit unbrauchbar; Quelle/Exportdefinition prüfen |
| `MengeBG` | `quantity_sheet` | 100 % leer | derzeit unbrauchbar; Quelle/Exportdefinition prüfen |

### Qualitätsbefund

- Für 1.005 Buchungszeilen beziehungsweise 83 Auftragsnummern gibt es keine
  Rohwarenposition. Diese Datensätze müssen sichtbar bleiben.
- Die Kombination Auftrag + Artikel deckt 90,879 % der Buchungszeilen in den
  Rohwarenpositionen ab; dies ist noch keine eindeutige Positionszuordnung.
- **OFFEN:** stabile Buchungs-ID ergänzen oder vom Quellsystem definieren lassen.
- **OFFEN:** Datum 2026-12-23 als zulässige Zukunftsbuchung oder Datenfehler klären.

---

## SRC-005 – Fertigungsmaterial

### Tabellenbeschreibung

- **Datei:** `Fertigungsmaterial.csv`
- **Logischer Tabellenname:** `production_material_usage`
- **Zeilen:** 151.837
- **Eine Zeile entspricht:** plausibel einem Materialverbrauch je Auftrag, Artikel
  und Gruppe; fachlich bestätigen.
- **Schlüssel:** (`Auftrag`, `Artikel`, `Gruppe`) ist nicht eindeutig: 1 Zeile hat
  einen unvollständigen Kandidaten, 5 weitere Zeilen duplizieren den Kandidaten.
- **Beziehung zum Auftragskopf:** 100 % über `Auftrag` → `BelegNummer`.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Auftrag` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `Artikel` | `article_number` | gemischte ID, 1 leer | als Text importieren; Artikelquelle offen |
| `Preis` | `material_price` | Dezimalzahl, 24,414 % leer | immer per 1 und EUR|
| `Gruppe` | `material_group_code` | gemischte ID, 1 leer | als Text importieren |
| `Bezeichnung` | `material_description` | Text, 1 leer | Freitext/Bezeichnung |
| `GruppeBezeichnung` | `material_group_name` | Text, vollständig | 16 Ausprägungen beobachtet |
| `VerbrauchteMenge` | `consumed_quantity` | Dezimalzahl, vollständig | Einheit und Aggregationsgrad offen |
| `Materialwert` | `material_value` | Dezimalzahl, vollständig | EUR ; 37.547 Nullwerte |

### Qualitätsbefund

- Auftrag ist vollständig referenziell gedeckt.
- Für Wellkarton ist `Fertigungsmaterial.csv` die vorgelagerte BDE-Erfassung.
  Maßgeblicher Nachweis für die statische Prüfung ist erst die anschließend
  übertragene Buchung in `RW_Buchungen.csv`.
- Nur 11,146 % der Kombinationen Auftrag + Artikel finden sich exakt in
  `RW_Buchungen.csv`, nur 8,499 % in `RohwarenPos.csv`.
- **OFFEN:** Sind Artikelnummern unterschiedlich formatiert, stammen sie aus
  verschiedenen Artikelräumen oder beschreibt die Tabelle eine andere Materialebene?
- **OFFEN:** stabilen Positions-/Verbrauchsschlüssel bereitstellen.

---

## SRC-006 – Produktionszeiten

### Tabellenbeschreibung

- **Datei:** `ProdZeiten.csv`
- **Logischer Tabellenname:** `production_time_entry`
- **Zeitraum:** 2023-01-03 bis 2026-08-12
- **Zeilen:** 398.869
- **Eine Zeile entspricht:** plausibel einer Produktionszeitmeldung je Auftrag,
  Arbeitsvorgang und Kostenstelle; fachlich bestätigen.
- **Schlüssel:** keine Ereignis-ID vorhanden. Ein getesteter zusammengesetzter
  Kandidat ist wegen 17.972 unvollständiger Schlüssel nicht geeignet.
- **Beziehung zum Auftragskopf:** 100 % über `Auftrag`.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Datum` | `entry_date` | Datum, 88 leer/ungültig | Pflichtfeldstatus und Behandlung fehlender Daten klären |
| `Mehraufwand Id` | `additional_effort_id` | ID, 94,692 % leer | Mögliche Störungen bzw. Mehraufwände die Leistung reduzieren können|
| `Auftrag` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `Kosten` | `cost_amount` | numerisch, vollständig | immer EURO- Nullwerte sind Personenzeiten|
| `Dauer` | `duration` | Dezimalzahl, vollständig | Einheit und Rundung offen |
| `DauerMaschine` | `machine_duration` | Dezimalzahl, vollständig | Einheit und Abgrenzung offen |
| `DauerMF` | `mf_duration` | Dezimalzahl, vollständig | Dauer des Maschinenführers- sollte Analgezeit/Maschinenstunden entsprechen |
| `Menge` | `reported_quantity` | numerisch, vollständig | Einheit; 291.176 Nullwerte |
| `Bogen` | `sheet_quantity` | numerisch, vollständig | Einheit/Bedeutung; 291.179 Nullwerte |
| `Stück` | `piece_quantity` | numerisch, vollständig | Einheit/Bedeutung; 291.176 Nullwerte |
| `ARVONR` | `operation_number` | Ganzzahl, vollständig | Arbeitsvorgangsnummer  |
| `ARVOKurz` | `operation_short_name` | Text, vollständig | Kurzbezeichnung zum Arbeitsvorgang vermutet |
| `KSTKurz` | `cost_center_short_name` | Text, 4,498 % leer | Kostenstellenbezug  |
| `KSTBezeichnung` | `cost_center_name` | Text, 4,498 % leer | Kostenstellenbezeichnung  |
| `KSTNrKurz` | `cost_center_short_number` | Text, 4,498 % leer | Kostenstellenschlüssel  |
| `Stufe` | `production_stage_code` | Text, 10,355 % leer | Werteliste Produktionsstufe als ID/Nr |
| `Stufe Bezeichnung` | `production_stage_name` | Text, 10,355 % leer | Bezeichnung zur Stufe  |

### Qualitätsbefund

- Die Datei ist syntaktisch gut, benötigt aber eine stabile Ereignis-ID.
- Eine Verknüpfung mit der entfernten Mengenmeldungsdatei ist nicht mehr Teil des
  aktuellen Datenmodells.
- **OFFEN:** 88 fehlende/ungültige Datumswerte fachlich behandeln.

---

## SRC-007 – Produktionsplanung

### Tabellenbeschreibung

- **Datei:** `Planung.csv`
- **Logischer Tabellenname:** `production_plan_entry`
- **Zeilen:** 264.707
- **Eine Zeile entspricht:** technisch einem eindeutigen Planungsdatensatz;
  fachliches Korn und Versionierungslogik sind noch zu bestätigen.
- **Primärschlüsselkandidat:** `Id`, vollständig und eindeutig.
- **Beziehung zum Auftragskopf:** 100 % über `AuftragNr` → `BelegNummer`.
- **Beziehung zu Produktionszeiten:** Auftrag + `Stufe` trifft nur für 29,349 %
  der Planungszeilen; das ist keine vollständige Zuordnung einzelner Plan- und
  Ist-Meldungen. `Produktionskostenstelle Id` und `KSTNrKurz` haben 0 % direkte
  Übereinstimmung und liegen offenbar in unterschiedlichen Schlüsselräumen.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Id` | `planning_entry_id` | Ganzzahl, eindeutig und vollständig | technischer Primärschlüsselkandidat; Stabilität über Exporte bestätigen |
| `Stufe Id` | `stage_id` | Ganzzahl, 46,112 % leer | technischer Stufenschlüssel; Abgrenzung zu `Stufe Nr` und `Stufe` offen |
| `Auftrag Nr + Bogen Nr` | `order_sheet_reference` | Text, vollständig | zusammengesetzte Anzeige-/Referenzangabe; Aufbau und Bogenanteil offen |
| `Produktionskostenstelle Id` | `production_cost_center_id` | Ganzzahl, 46,110 % leer | Kostenstellen-ID; ohne Mapping kein Join zu `ProdZeiten.KSTNrKurz` |
| `Plandatum` | `planned_date` | Datum, 54,504 % leer | 71 Werte im Jahr 1899 und ein Wert im Jahr 2018 sind zu prüfen |
| `PlanMenge` | `planned_quantity` | Dezimalzahl, 73,230 % leer | Einheit und Grund für hohe Leerquote offen |
| `Rüstzeit` | `planned_setup_time` | Dezimalzahl, 5 Werte leer | Einheit und Rundung offen |
| `Laufzeit` | `planned_run_time` | Dezimalzahl, 11,906 % leer | Einheit und Rundung offen |
| `Planzeit` | `planned_total_time` | Dezimalzahl, 7 Werte leer | entspricht bei 233.154 von 233.185 vollständig befüllten Zeilen innerhalb 0,001 der Summe aus Rüst- und Laufzeit |
| `Sollleistung1` | `target_performance` | Dezimalzahl, 4,021 % leer | Formel, Einheit und Bezugsgröße offen |
| `Fertigdatum` | `completion_date` | Datum, 13,779 % leer | Zeitraum 2023-01-03 bis 2026-08-12 |
| `Stufe Nr` | `stage_number` | Ganzzahl, vollständig | 26 Ausprägungen; Beziehung zu `Stufe Id` offen |
| `AuftragNr` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `Stufe` | `stage_code` | Text, vollständig | 26 Ausprägungen; nur teilweise Übereinstimmung mit Produktionszeiten |
| `AuftragFertigDatum` | `order_completion_timestamp` | numerischer Excel-Zeitwert, 156 Werte leer | Werte entsprechen 2023-01-03 bis 2026-08-12; beim Import explizit aus Excel-Serienzahl konvertieren |
| `STANZFORM` | `die_cutting_form` | Text, 89,255 % leer | Bedeutung, Schlüsselraum und Vertraulichkeit offen |
| `PlanungAktivStatus` | `planning_active_status` | Text, vollständig, 2 Ausprägungen | Werteliste und Bedeutung für historische Planstände offen |

### Qualitätsbefund

- `Id` und Auftragsbezug sind technisch gut geeignet.
- `AuftragFertigDatum` ist kein CSV-Datumsstring, sondern eine Excel-Serienzahl
  mit Tagesbruchteil; ein normaler Datumsparser würde das Feld falsch behandeln.
- **OFFEN:** Sind Zeilen mit leerer Stufen-/Kostenstellen-ID Auftrags- oder
  Summenzeilen, und dürfen sie mit Arbeitsgangszeilen zusammen ausgewertet werden?
- **OFFEN:** Sind die historischen `Plandatum`-Werte 1899/2018 gültig, Platzhalter
  oder Datenfehler?
- **OFFEN:** Welche Felder verbinden Planung und tatsächliche Produktionszeit auf
  der gewünschten Granularität (z. B. Arbeitsgang-ID, Kostenstellen-Mapping)?

---

## SRC-008 – Kostenträgerbuchungen

### Tabellenbeschreibung

- **Datei:** `KTRBuchungenKI.csv`
- **Logischer Tabellenname:** `cost_object_booking`
- **Zeitraum:** 2023-01-20 bis 2026-08-10
- **Zeilen:** 13.827
- **Eine Zeile entspricht:** plausibel einer Kostenträgerbuchung; fachlich bestätigen.
- **Schlüssel:** keine Buchungs-ID. Ein getesteter zusammengesetzter Kandidat hat
  27 Duplikatzeilen; außerdem existieren 23 vollständig identische Zeilen.
- **Beziehung zum Auftragskopf:** 100 % über `KostenTraeger` → `BelegNummer`.
- `Kostenträger Key` passt weder auf `BelegKopfKey` noch auf `V_BelegKopf_Obj`.

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Kostenträger Key` | `cost_object_key` | Text, vollständig | technischer Schlüssel, aber nicht Auftragskopf-Schlüssel |
| `KTRKostenart Key` | `cost_type_key` | Text, vollständig | Kostenart-Fremdschlüssel vermutet |
| `BuchungsDatum` | `booking_date` | Datum, vollständig | Buchungsdatum |
| `KostenTraeger` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `TrKoArt` | `cost_type_code` | Ganzzahl, vollständig | 3 Ausprägungen; Beziehung zu Kostenart-Key offen |
| `Betrag` | `amount` | Dezimalzahl, vollständig | Währung/Vorzeichen offen; 203 negative Werte |
| `Menge` | `quantity` | Dezimalzahl, vollständig | Einheit/Vorzeichen offen; 68 negative Werte |
| `BuchungsText` | `booking_text` | Text, 0,043 % leer | Freitext; kann verwendet werden|

### Qualitätsbefund

- **OFFEN:** Sind die 23 identischen Zeilen echte Mehrfachbuchungen 
- **OFFEN:** stabile Buchungs-ID und Kostenartenstamm bereitstellen.

---

## SRC-009 – Rechnungskontrollen

### Tabellenbeschreibung

- **Datei:** `Rechnungskontrollen.csv`
- **Logischer Tabellenname:** `invoice_control_item`
- **Zeitraum:** 2023-01-04 bis 2026-08-11
- **Zeilen:** 9.499
- **Eine Zeile entspricht:** plausibel einer Rechnungskontrollposition;
  fachlich bestätigen.
- **Schlüssel:** weder (`ReferenzNr`, `Artikel Key`, `Traeger`) noch
  (`BelegNummer`, `Artikel Key`, `Traeger`) ist eindeutig.
- **Exakte doppelte Zeilen:** 407
- **Beziehung zum Auftragskopf:** 100 % über `Traeger` → `BelegNummer`.
- **Artikelbeziehung:** `Artikel Key` hat nahezu keine exakten Treffer in den
  Rohwarentabellen; vermutlich anderer Schlüsselraum oder andere Artikelart.

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `ReferenzNr` | `reference_number` | ziffernartige ID, vollständig | nicht identisch zu `BelegNummer`; eindeutige Nummer |
| `BelegNummer` | `invoice_document_number` | ziffernartige ID, vollständig | Belegbedeutung offen; Rechnungskontrollnummer |
| `RechnungsDatum` | `invoice_date` | Datum, vollständig | Rechnungsdatum plausibel |
| `GutschriftErzeugen` | `create_credit_note_code` | Ganzzahl, 2 Ausprägungen | Codewerte und Prozesswirkung offen |
| `Lieferant Key` | `supplier_key` | Text, vollständig | Fremdschlüssel zu fehlendem Lieferantenstamm vermutet |
| `Artikel Key` | `invoice_article_key` | Text, vollständig | Aufbau: Firmenschlüssel, Trenner `|`, danach Artikel; Artikelpräfix `WS` kennzeichnet WS-Leistungen, `EF` Stanzformartikel |
| `ArtikelGruppe` | `article_group_code` | gemischte ID, vollständig | als Text importieren; 24 Ausprägungen |
| `Bezeichnung` | `description` | Text, vollständig | Freitext/Artikelbezeichnung |
| `Menge` | `invoice_quantity` | Dezimalzahl, vollständig | Einheit/Vorzeichen offen; 145 negative Werte |
| `WarenwertEUR` | `goods_value_eur` | Dezimalzahl, vollständig | EUR laut Name; 145 negative Werte |
| `Traeger` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |

### Qualitätsbefund

- **OFFEN:** Sind 407 identische Zeilen Duplikate fachlich zulässige
- `ReferenzNr` und `BelegNummer` sind in keiner Zeile identisch; beide Definitionen
  müssen bereitgestellt werden.
- **OFFEN:** Negative Mengen/Werte als Gutschrift oder Storno bestätigen.

---

## SRC-010 – Faktura je Auftrag

### Tabellenbeschreibung

- **Datei:** `Faktura.csv`
- **Logischer Tabellenname:** `order_billing_summary`
- **Zeilen:** 27.334
- **Eine Zeile entspricht:** technisch einer eindeutigen Faktura-Zusammenfassung
  je Auftrag; fachlich bestätigen, ob immer der aktuelle Gesamtstand exportiert wird.
- **Eindeutige Schlüssel:** `Auftrag` und `Auftrag_BelegKopfKey` jeweils einzeln.
- **Beziehung zum Auftragskopf:** beide Schlüssel haben 100 % Treffer.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Auftrag` | `order_number` | ziffernartige ID, eindeutig und vollständig | FK zu `Auftragskopf.BelegNummer` bestätigt |
| `Auftrag_BelegKopfKey` | `order_header_key` | Text, eindeutig und vollständig | FK zu `Auftragskopf.BelegKopfKey` bestätigt |
| `Summe_Rechnung_EUR` | `invoice_amount_eur` | Dezimalzahl, vollständig | aggregierte Rechnungssumme in EUR; Brutto-/Nettoabgrenzung offen |
| `Summe_Gutschrift_EUR` | `credit_amount_eur` | Dezimalzahl, vollständig | aggregierte Gutschrift in EUR; überwiegend positiv gespeichert, 1 negativer Wert ist zu klären |
| `Erloes_EUR` | `billed_revenue_eur` | Dezimalzahl, vollständig | technisch in allen 27.334 Zeilen: Rechnungssumme minus Gutschriftssumme |
| `Anzahl_Rechnungen` | `invoice_count` | Ganzzahl, vollständig | Anzahl zugrunde liegender Rechnungen; 95 Aufträge ohne Rechnung |
| `Anzahl_Gutschriften` | `credit_note_count` | Ganzzahl, vollständig | Anzahl Gutschriften; 25.923 Aufträge ohne Gutschrift |
| `Rechnungsnummern` | `invoice_numbers` | Textliste, 0,348 % leer | Einzelwert oder mehrere Werte mit Pipe-Zeichen; nicht als atomarer Schlüssel verwenden |
| `Gutschriftnummern` | `credit_note_numbers` | Textliste, 94,838 % leer | Einzelwert oder mehrere Werte mit Pipe-Zeichen |
| `Rechnung_BelegKopfKeys` | `invoice_header_keys` | Textliste, 0,348 % leer | Pipe-getrennte Liste; Normalisierung in Kindtabelle empfohlen |
| `Gutschrift_BelegKopfKeys` | `credit_note_header_keys` | Textliste, 94,838 % leer | Pipe-getrennte Liste; Normalisierung in Kindtabelle empfohlen |

### Qualitätsbefund

- Anzahl 0 und leere Nummern-/Schlüssellisten sind für Rechnungen und
  Gutschriften in allen Zeilen konsistent.
- Die Erlösformel ist technisch vollständig konsistent. Ihre fachliche
  Verwendbarkeit gegenüber `Auftragskopf.Erlöse` und `GesamtNettoEUR` muss noch
  definiert werden, da diese Felder laut Katalog auch erwartete Erlöse enthalten.
- **OFFEN:** Sind die Beträge netto oder brutto, enthalten sie Steuer, Skonto,
  Bonus oder Fremdwährungseffekte, und welcher Buchungsstichtag gilt?
- **OFFEN:** Soll die Fakturaquelle nur als Auftragsaggregation verwendet werden,
  oder werden zusätzlich einzelne Rechnungs-/Gutschriftpositionen benötigt?

---

## Bestätigte und verworfene Beziehungen

| Kind/Feld | Eltern/Feld | Treffer auf Zeilenebene | Bewertung |
|---|---|---:|---|
| Vertriebsposition.`BelegKopfKey` | Auftragskopf.`BelegKopfKey` | 100 % | technisch bestätigt |
| Rohwarenposition.`BelegKopf Key` | Auftragskopf.`BelegKopfKey` | 100 % | technisch bestätigt |
| Fertigungsmaterial.`Auftrag` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Produktionszeit.`Auftrag` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Planung.`AuftragNr` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Faktura.`Auftrag` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Faktura.`Auftrag_BelegKopfKey` | Auftragskopf.`BelegKopfKey` | 100 % | technisch bestätigt |
| KTR-Buchung.`KostenTraeger` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Rechnungskontrolle.`Traeger` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| RW-Buchung.`BelegNummer` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| RW-Buchung.`BelegNummer` | Rohwarenposition.`BelegNummer` | 98,473 % | Zuordnung nur auf Auftragsebene |
| RW-Buchung Auftrag + Artikel | Rohwarenposition Auftrag + Artikel | 90,879 % | nicht eindeutig; keine Positionszuordnung |
| Rohwarenposition Kopf + Position | Vertriebsposition Kopf + Position | 0 % | als direkte Beziehung verworfen |
| Planung Auftrag + `Stufe` | Produktionszeit Auftrag + `Stufe` | 29,349 % | nur Teilabdeckung; keine Ereigniszuordnung |
| Planung Auftrag + Kostenstellen-ID | Produktionszeit Auftrag + `KSTNrKurz` | 0 % | unterschiedliche Schlüsselräume; Mapping nötig |
| KTR.`Kostenträger Key` | Auftragskopf-Schlüssel | 0 % | Schlüsselräume verschieden |
| Rechnungskontrolle.`Artikel Key` | Rohwaren-`Artikel Key` | höchstens 1,253 % | vermutlich verschiedene Artikelräume |

## Priorisierte offene Fragen

1. Welcher Auftragskopf-Schlüssel ist dauerhaft und systemübergreifend verbindlich:
   `BelegKopfKey`, `V_BelegKopf_Obj` oder `BelegNummer`?
2. Welcher Schlüssel verbindet eine Rohwarenposition mit einer Vertriebsposition?
3. Welche eindeutigen Buchungs-/Meldungs-IDs existieren für RW-Buchungen,
   Fertigungsmaterial, Produktionszeiten, KTR-Buchungen und Rechnungskontrollen?
4. Welche Einheiten gelten für alle Mengen-, Dauer-, Bogen-, Stück- und Gewichtsfelder?
5. Welche Währungen, Preisbasen, Rundungen und Vorzeichenregeln gelten?
6. Wie werden Storno, Gutschrift, Rückbuchung und negative Mengen unterschieden?
7. Sind Nullwerte echte Nullmengen/-werte oder Ersatz für fehlende Informationen?
8. Sind die identischen Zeilen in KTR-Buchungen und Rechnungskontrollen zulässig?
9. Warum enthält `RW_Buchungen.csv` ein Buchungsdatum bis 2026-12-23?
10. Welche Wertelisten gelten für Status-, Offen-, Naka-, Kostenart-, Einheiten-
    und Zusatzkostenfelder?
11. Wie werden `Stufe Id`, `Stufe Nr` und `Stufe` voneinander abgegrenzt, und
    welches Mapping verbindet `Produktionskostenstelle Id` mit den Kostenstellen
    der Produktionszeiten?
12. Was bedeuten die historischen Planungsdaten 1899/2018, und wann sind leere
    Planfelder fachlich zulässig?
13. Sind Fakturabeträge netto oder brutto, und welcher Buchungs-/Exportstichtag gilt?
14. Welche fehlenden Stamm- und Datentabellen werden noch geliefert, insbesondere
    Artikel, Kunde, Lieferant, Vertreter, Kostenstelle und Kostenart?
15. Dürfen Freitextfelder wie `Zusatztext`, `BuchungsText`, `NakaBem` und `Muster`
    für KI-Analysen verwendet werden, oder enthalten sie schützenswerte Inhalte?

## Freigabe

- **Fachlich geprüft durch:** **OFFEN**
- **Technisch geprüft durch:** lokale Strukturprüfung durch Codex; fachliche
  Validierung ausstehend
- **Freigabestatus:** Entwurf
- **Nächste Überprüfung:** nach Beantwortung der priorisierten offenen Fragen oder
  Lieferung weiterer Tabellen
