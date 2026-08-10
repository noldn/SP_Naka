# Datenkatalog SP_Naka

Dieser Katalog beschreibt die lokal bereitgestellten Datenquellen anhand einer
strukturellen Prüfung vom 2026-08-10. Er enthält keine echten Datensätze oder
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
- Es fehlen laut Projektangabe noch zwei bis drei Datenquellen.
- Verantwortlichkeit, Aktualisierungsrhythmus, Aufbewahrung und Freigabestatus
  können nicht aus den Dateien abgeleitet werden.

## Technische Beurteilung der CSV-Dateien

Alle neun Dateien sind technisch lesbar und grundsätzlich für eine automatisierte
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

## Übergreifende offene Angaben

- **OFFEN:** Handelt es sich je Datei um einen Vollbestand, einen Stichtag oder
  eine Änderungslieferung?
- **OFFEN:** Wie oft werden die Dateien geliefert und wann ist ein Export vollständig?
- **OFFEN:** Welche Zeitzone gilt für Datums- und Zeitfelder?
- **OFFEN:** Welche Währung gilt für Felder ohne `EUR` im Namen?
- **OFFEN:** Welche Mengeneinheiten und Umrechnungsregeln gelten je Tabelle?
- **OFFEN:** Bedeutet leer immer „nicht vorhanden“, oder teilweise „unbekannt“?
- **OFFEN:** Welche Vertraulichkeitsstufe, Aufbewahrungsfrist und Löschregel gilt?
- **OFFEN:** Welche Status- und Codewertelisten existieren im Quellsystem?

## Übersicht der Datenquellen

| ID | Datei | Logischer Tabellenname | Zeilen | Spalten | Technisch beobachtetes Tabellenkorn | Schlüsselstatus |
|---|---|---|---:|---:|---|---|
| SRC-001 | `Auftragskopf.csv` | `order_header` | 38.794 | 20 | eine eindeutige Auftragskopfzeile | drei eindeutige Kennungen bestätigt |
| SRC-002 | `VertriebsPositionen.csv` | `sales_order_item` | 108.072 | 19 | eine eindeutige Vertriebsposition | Einzel- und zusammengesetzter Schlüssel bestätigt |
| SRC-003 | `RohwarenPos.csv` | `raw_material_item` | 45.433 | 24 | eine eindeutige Rohwaren-/Belegposition | mehrere eindeutige Kennungen bestätigt |
| SRC-004 | `RW_Buchungen.csv` | `raw_material_booking` | 65.631 | 10 | vermutlich eine Rohwarenbuchung | kein stabiler Einzelbelegschlüssel vorhanden |
| SRC-005 | `Fertigungsmaterial.csv` | `production_material_usage` | 151.520 | 8 | vermutlich ein Materialverbrauch je Auftrag/Artikel/Gruppe | Kandidat nicht eindeutig |
| SRC-006 | `ProdZeiten.csv` | `production_time_entry` | 397.890 | 17 | vermutlich eine Produktionszeit-/Arbeitsgangmeldung | keine Ereignis-ID vorhanden |
| SRC-007 | `MegenMeldung.csv` | `quantity_report` | 198.513 | 5 | vermutlich eine Mengenmeldung | `ZeitmeldungID` eindeutig |
| SRC-008 | `KTRBuchungenKI.csv` | `cost_object_booking` | 13.787 | 8 | Summierte Kostenträgerbuchungen von gewissen Kostenarten die nicht anderweitig erfasst wurden | Summierte Buchungen |
| SRC-009 | `Rechnungskontrollen.csv` | `invoice_control_item` | 9.480 | 12 | Rechnungskontrollpositionen die für den Auftrag angeschafft werden, wie. Z.B. Werkzeuge oder Spezialmaterialien oder Fremdarbeit | kein eindeutiger Schlüssel bestätigt |

---

## SRC-001 – Auftragskopf

### Tabellenbeschreibung

- **Datei:** `Auftragskopf.csv`
- **Logischer Tabellenname:** `order_header`
- **Zeitraum:** 2023-01-01 bis 2026-08-06
- **Zeilen:** 38.794
- **Eine Zeile entspricht:** technisch einer eindeutigen Kopfzeile;
- **Eindeutige Schlüssel:** `BelegKopfKey`, `V_BelegKopf_Obj` und `BelegNummer`
- **Bevorzugter logischer Schlüssel:** `BelegKopfKey` als `order_header_key`;
  **OFFEN:** fachlich bestätigen, welcher Schlüssel systemübergreifend stabil ist.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `BelegDatum` | `order_date` | Datum, 100 % befüllt | Belegdatum des auftrages/BEstelldatum des Kunden. Relevantes Datum für Auswertungen |
| `V_BelegKopf_Obj` | `order_header_object_id` | Text, eindeutig, vollständig | technischer Schlüssel; ISt eindeutisger sChlüssel, wird aber aktuell nicht in anderen Tabellen verwendet |
| `BelegKopfKey` | `order_header_key` | Text, eindeutig, vollständig | Primärschlüssel |
| `Kunde Key` | `customer_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Kundenstamm  |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Boolean- auftrag arhiviertd und Abgeschlossen oder noch Offen |
| `BelegNummer` | `order_number` | ziffernartige ID, eindeutig | fachliche Auftragsnummer; als Text importieren |
| `Zusatztext` | `additional_text` | Text, vollständig | Freitext; Auftrags/Projektbeschreibung |
| `X_ArtikelGruppe` | `article_group_code` | gemischte ID, 4,367 % leer | als Text importieren; Artikelgruppe- Welche Produktkategorie soll Produziert werden |
| `ArtikelGruppeBez` | `article_group_name` | Text, vollständig | Bezeichnung; 37 Ausprägungen beobachtet Artikelgruppe- Welche Produktkategorie soll Produziert werden |
| `Erlöse` | `revenue_amount` | Dezimalzahl, vollständig | Berechnete Erlöse des Autrags in EUR; Tatsächliche erlöse + Erlöse die aufgrund des Bestands zu erwarten sind. Mögliche Gutschriften/Bonus sind inkludiert |
| `Kosten` | `cost_amount` | Dezimalzahl, vollständig | Summe der osten lt. Nachkalkulation in EUR 5 negative Werte |
| `Produktionsstatus` | `production_status` | Text, 2 Ausprägungen | Sollten nur Fertige oder Stornierte Aufträge sein- sind in der Produktion abgehsclossen, Diverse Leistungen können zukünftig noch anfallen, Versand, Lagerhaltung,.. |
| `AuftragStatus` | `order_status_code` | Ganzzahl, 2 Ausprägungen | Werteliste und Abgrenzung zu `Status` offen |
| `NakaOK` | `naka_ok_code` | Ganzzahl, 2 Ausprägungen | fachliche Prüflogik offen |
| `NakaBem` | `naka_comment` | Text, 99,995 % leer | nur 2 befüllte Zeilen; Notwendigkeit und Vertraulichkeit prüfen |
| `AuftragsArt` | `order_type` | Text, 5 Ausprägungen | Werteliste offen |
| `MargenTage` | `margin_days` | Zahl, vollständig | überwiegend ganzzahlig, 10 Dezimalwerte; Berechnung/Rundung offen |
| `Vertreter Key` | `sales_representative_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Vertreterstamm vermutet |
| `Status` | `status_text` | Text, 2 Ausprägungen | Abgrenzung zu Auftrag-/Produktionsstatus offen |
| `GesamtNettoEUR` | `total_net_eur` | Dezimalzahl, vollständig | EUR laut Name; 1 negativer und 12.559 Nullwerte fachlich prüfen |

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
- **Zeilen:** 108.072
- **Eine Zeile entspricht:** technisch einer eindeutigen Vertriebsposition;
  fachliche Bestätigung steht aus.
- **Eindeutige Schlüssel:** `V_BelegPos_Obj` sowie
  (`BelegKopfKey`, `PositionsNr`)
- **Beziehung zum Auftragskopf:** 102.726 von 108.072 Zeilen (95,053 %) passen
  über `BelegKopfKey`; 5.346 Zeilen beziehungsweise 1.610 verschiedene
  Kopf-Schlüssel haben keinen Treffer.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Firma` | `company_code` | Ganzzahl, konstant | **OFFEN:** Bedeutung des Codes; für Mehrfirmenfähigkeit als Schlüsselteil vorsehen |
| `Artikel Key` | `article_key` | Text, vollständig | Fremdschlüssel zu noch fehlendem Artikelstamm vermutet |
| `BelegKopfKey` | `order_header_key` | Text, vollständig | FK zu `order_header`; nicht vollständig referenziell gedeckt |
| `PositionsNr` | `sales_item_number` | numerisch, vollständig | Teil des eindeutigen zusammengesetzten Schlüssels; 4 Dezimaldarstellungen prüfen |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Codewerte offen |
| `WertPosition` | `is_value_item_code` | Ganzzahl, 2 Ausprägungen | Bedeutung offen |
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren; führende Nullen erhalten |
| `Menge` | `ordered_quantity` | Dezimalzahl, vollständig | **OFFEN:** Einheit und Bedeutung der 14.812 Nullwerte |
| `gelieferte_Menge` | `delivered_quantity` | Dezimalzahl, vollständig | **OFFEN:** Einheit; 37.020 Nullwerte |
| `Einzelpreis` | `unit_price` | Dezimalzahl, vollständig | **OFFEN:** Währung und Preisbasis; 4 negative Werte |
| `EinzelpreismZuAbschl` | `unit_price_after_adjustment` | Dezimalzahl, vollständig | genaue Berechnungslogik/Abgrenzung zu `Einzelpreis` offen |
| `Zusatzkostentyp` | `additional_cost_type_code` | Ganzzahl, 4 Ausprägungen | Werteliste offen |
| `KommissionsNr` | `commission_number` | ID, 13,634 % leer | Bedeutung und Beziehung zu `Komm Key` offen |
| `Preiseinheitsfaktor` | `price_unit_factor` | positive Ganzzahl, vollständig | Einheit und Anwendung in Preisformeln offen |
| `KundenArtikelNr` | `customer_article_number` | gemischte ID, 8,374 % leer | als Text importieren; Fremdschlüssel/Verwendung offen |
| `GesamtNetto` | `total_net_amount` | Dezimalzahl, vollständig | **OFFEN:** Währung und Berechnung; 4 negative Werte |
| `Stornierte_Menge` | `cancelled_quantity` | Dezimalzahl, vollständig | Vorzeichenlogik offen; 86 negative Werte |
| `V_BelegPos_Obj` | `sales_item_object_id` | Text, eindeutig, vollständig | stabiler Einzel-Schlüsselkandidat |
| `Muster` | `sample_code_or_text` | Text, vollständig | **OFFEN:** fachliche Bedeutung und mögliche Vertraulichkeit |

### Qualitätsbefund

- Positionsschlüssel sind technisch sehr gut geeignet.
- **OFFEN:** Warum fehlen zu 5.346 Positionen passende Auftragsköpfe? Mögliche
  Ursachen wie unterschiedliche Exportfilter oder Löschstände müssen geprüft werden.
- Numerisch wirkende Positions- und Artikelnummern dürfen nicht automatisch in
  Zahlen umgewandelt werden.

---

## SRC-003 – Rohwarenpositionen

### Tabellenbeschreibung

- **Datei:** `RohwarenPos.csv`
- **Logischer Tabellenname:** `raw_material_item`
- **Zeitraum Anlage:** 2023-01-02 bis 2026-08-07
- **Zeitraum Änderung:** 2023-01-09 bis 2026-08-08
- **Zeilen:** 45.433
- **Eine Zeile entspricht:** technisch einer eindeutigen Belegposition;
  **OFFEN:** fachlich klären, ob dies eine geplante, bestellte, reservierte oder
  gelieferte Rohwarenposition ist.
- **Eindeutige Schlüssel:** `BelegposKey`, `BelegposBelegArtKey`,
  `VertriebAuftrag_Pos`, `V_BelegPos_Obj` sowie
  (`BelegKopf Key`, `PositionsNr`)
- **Beziehung zum Auftragskopf:** 42.704 von 45.433 Zeilen (93,993 %) passen;
  2.729 Zeilen beziehungsweise 1.271 Kopf-Schlüssel fehlen im Auftragskopf.
- **Beziehung zu Vertriebspositionen:** weder `VertriebAuftrag_Pos` gegen
  `V_BelegPos_Obj` noch die Kombination Kopf + Position liefert Treffer.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Firma` | `company_code` | Ganzzahl, konstant | Firmenkontext offen |
| `Artikel Key` | `article_key` | Text, vollständig | Fremdschlüssel zu Artikelstamm vermutet |
| `BelegKopf Key` | `order_header_key` | Text, vollständig | FK-Kandidat zum Auftragskopf; 6,007 % der Zeilen ohne Treffer |
| `Komm Key` | `commission_key` | Text, vollständig | Beziehung zu `KommissionsNr` offen |
| `BelegposKey` | `document_item_key` | Text, eindeutig | bevorzugter lokaler Primärschlüsselkandidat |
| `BelegposBelegArtKey` | `document_item_type_key` | Text, eindeutig | Abgrenzung zu `BelegposKey` offen |
| `VertriebAuftrag_Pos` | `sales_order_item_reference` | Text, eindeutig | kein direkter Treffer auf Vertriebspositionsschlüssel; Formatdefinition nötig |
| `PositionsNr` | `raw_material_item_number` | numerisch, vollständig | 2 Dezimaldarstellungen; offenbar nicht Vertriebspositionsnummer |
| `BelegArt` | `document_type` | Text, konstant | Bedeutung/Filterwirkung offen |
| `ReferenzNr` | `reference_number` | ziffernartige ID, vollständig | Beziehung zu `BelegNummer`/Auftrag offen |
| `BelegNummer` | `order_number` | ziffernartige ID, vollständig | gleiche Abdeckung zum Auftragskopf wie Kopf-Key |
| `offen` | `is_open_code` | Ganzzahl, 2 Ausprägungen | Werteliste offen |
| `WertPosition` | `is_value_item_code` | Ganzzahl, 2 Ausprägungen | Werteliste offen |
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren |
| `Menge` | `ordered_quantity` | Dezimalzahl, vollständig | Einheit über Codefeld; 159 Nullwerte |
| `gelieferte_Menge` | `delivered_quantity` | Dezimalzahl, vollständig | 1 negativer Wert; Storno-/Korrekturlogik offen |
| `reservierte_Menge` | `reserved_quantity` | Dezimalzahl, vollständig, immer 0 | derzeit ohne Informationsgehalt; Exportdefinition prüfen |
| `MengenEinheit` | `quantity_unit_code` | Ganzzahlcode, 5 Ausprägungen | zwingend Werteliste/Umrechnung bereitstellen |
| `Zusatzkostentyp` | `additional_cost_type_code` | Ganzzahl, 3 Ausprägungen | Werteliste offen |
| `Gesamtgewicht` | `total_weight` | Dezimalzahl, vollständig, immer 0 | derzeit ohne Informationsgehalt; Einheit/Export prüfen |
| `Stornierte_Menge` | `cancelled_quantity` | Dezimalzahl, vollständig | 543 negative Werte; Vorzeichenregel offen |
| `AenderungDatum` | `modified_date` | Datum, vollständig | Zeitanteil/Zeitzone offen |
| `AnlageDatum` | `created_date` | Datum, vollständig | Zeitanteil/Zeitzone offen |
| `V_BelegPos_Obj` | `raw_material_item_object_id` | Text, eindeutig | technischer Schlüsselkandidat; nicht mit Vertriebsobjekt gleichsetzen |

### Qualitätsbefund

- Die Datei ist positionsintern gut schlüsselbar, aber die fachliche Verbindung zur
  Vertriebsposition ist nicht definiert.
- `reservierte_Menge` und `Gesamtgewicht` enthalten ausschließlich Nullwerte.
- **OFFEN:** Verbindungsschlüssel oder Zuordnungsregel zwischen Rohwaren- und
  Vertriebspositionen bereitstellen.

---

## SRC-004 – Rohwarenbuchungen

### Tabellenbeschreibung

- **Datei:** `RW_Buchungen.csv`
- **Logischer Tabellenname:** `raw_material_booking`
- **Zeitraum:** 2023-01-05 bis 2026-12-23
- **Zeilen:** 65.631
- **Eine Zeile entspricht:** plausibel einer Materialbuchung;
  fachlich bestätigen.
- **Schlüssel:** keine Buchungs-ID vorhanden. Die Snapshot-Kombination
  (`BelegNummer`, `BuchungsDatum`, `Artikel Key`, `Menge`, `WertMat`) ist eindeutig,
  aber nicht als dauerhafter Primärschlüssel freigegeben.
- **Beziehung zum Auftragskopf:** 100 % über `BelegNummer`.
- **Beziehung zu Rohwarenpositionen:** 98,470 % der Buchungszeilen beziehungsweise
  99,659 % der verschiedenen Belegnummern kommen in `RohwarenPos.csv` vor.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Firma` | `company_code` | Ganzzahl, konstant | Firmenkontext offen |
| `Artikel` | `article_number` | gemischte ID, vollständig | als Text importieren |
| `Artikel Key` | `article_key` | Text, vollständig | Artikel-Fremdschlüsselkandidat |
| `S_Artikel_Obj` | `article_object_id` | Text, vollständig | Abgrenzung zu `Artikel Key` offen |
| `BelegNummer` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `BuchungsDatum` | `booking_date` | Datum, vollständig | ein Datum liegt nach dem aktuellen Analysestichtag; fachlich prüfen |
| `Menge` | `booked_quantity` | Dezimalzahl, vollständig | 55.114 negativ, 10.395 positiv; Vorzeichenlogik zwingend definieren |
| `WertMat` | `material_value` | Dezimalzahl, vollständig | 53.835 negativ; Währung und Vorzeichenlogik offen |
| `MengeKG` | `quantity_kg` | 100 % leer | derzeit unbrauchbar; Quelle/Exportdefinition prüfen |
| `MengeBG` | `quantity_sheet` | 100 % leer | derzeit unbrauchbar; Quelle/Exportdefinition prüfen |

### Qualitätsbefund

- Für 1.004 Buchungszeilen beziehungsweise 82 Auftragsnummern gibt es keine
  Rohwarenposition. Diese Datensätze müssen sichtbar bleiben.
- Die Kombination Auftrag + Artikel deckt 90,881 % der Buchungszeilen in den
  Rohwarenpositionen ab; dies ist noch keine eindeutige Positionszuordnung.
- **OFFEN:** stabile Buchungs-ID ergänzen oder vom Quellsystem definieren lassen.
- **OFFEN:** Datum 2026-12-23 als zulässige Zukunftsbuchung oder Datenfehler klären.

---

## SRC-005 – Fertigungsmaterial

### Tabellenbeschreibung

- **Datei:** `Fertigungsmaterial.csv`
- **Logischer Tabellenname:** `production_material_usage`
- **Zeilen:** 151.520
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
| `Preis` | `material_price` | Dezimalzahl, 24,417 % leer | Währung, Preisbasis und Grund für Leerwerte offen |
| `Gruppe` | `material_group_code` | gemischte ID, 1 leer | als Text importieren |
| `Bezeichnung` | `material_description` | Text, 1 leer | Freitext/Bezeichnung |
| `GruppeBezeichnung` | `material_group_name` | Text, vollständig | 16 Ausprägungen beobachtet |
| `VerbrauchteMenge` | `consumed_quantity` | Dezimalzahl, vollständig | Einheit und Aggregationsgrad offen |
| `Materialwert` | `material_value` | Dezimalzahl, vollständig | Währung/Berechnung offen; 37.467 Nullwerte |

### Qualitätsbefund

- Auftrag ist vollständig referenziell gedeckt.
- Nur 11,139 % der Kombinationen Auftrag + Artikel finden sich exakt in
  `RW_Buchungen.csv`, nur 8,497 % in `RohwarenPos.csv`.
- **OFFEN:** Sind Artikelnummern unterschiedlich formatiert, stammen sie aus
  verschiedenen Artikelräumen oder beschreibt die Tabelle eine andere Materialebene?
- **OFFEN:** stabilen Positions-/Verbrauchsschlüssel bereitstellen.

---

## SRC-006 – Produktionszeiten

### Tabellenbeschreibung

- **Datei:** `ProdZeiten.csv`
- **Logischer Tabellenname:** `production_time_entry`
- **Zeitraum:** 2023-01-03 bis 2026-08-08
- **Zeilen:** 397.890
- **Eine Zeile entspricht:** plausibel einer Produktionszeitmeldung je Auftrag,
  Arbeitsvorgang und Kostenstelle; fachlich bestätigen.
- **Schlüssel:** keine Ereignis-ID vorhanden. Ein getesteter zusammengesetzter
  Kandidat ist wegen 17.934 unvollständiger Schlüssel nicht geeignet.
- **Beziehung zum Auftragskopf:** 100 % über `Auftrag`.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `Datum` | `entry_date` | Datum, 88 leer/ungültig | Pflichtfeldstatus und Behandlung fehlender Daten klären |
| `Mehraufwand Id` | `additional_effort_id` | ID, 94,697 % leer | optionale Bedeutung/Beziehung offen |
| `Auftrag` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `Kosten` | `cost_amount` | numerisch, vollständig | Währung und Berechnung offen; 162.699 Nullwerte |
| `Dauer` | `duration` | Dezimalzahl, vollständig | Einheit und Rundung offen |
| `DauerMaschine` | `machine_duration` | Dezimalzahl, vollständig | Einheit und Abgrenzung offen |
| `DauerMF` | `mf_duration` | Dezimalzahl, vollständig | Bedeutung von MF und Einheit offen |
| `Menge` | `reported_quantity` | numerisch, vollständig | Einheit; 290.488 Nullwerte |
| `Bogen` | `sheet_quantity` | numerisch, vollständig | Einheit/Bedeutung; 290.491 Nullwerte |
| `Stück` | `piece_quantity` | numerisch, vollständig | Einheit/Bedeutung; 290.488 Nullwerte |
| `ARVONR` | `operation_number` | Ganzzahl, vollständig | Arbeitsvorgangsnummer vermutet |
| `ARVOKurz` | `operation_short_name` | Text, vollständig | Kurzbezeichnung zum Arbeitsvorgang vermutet |
| `KSTKurz` | `cost_center_short_name` | Text, 4,499 % leer | Kostenstellenbezug vermutet |
| `KSTBezeichnung` | `cost_center_name` | Text, 4,499 % leer | Kostenstellenbezeichnung vermutet |
| `KSTNrKurz` | `cost_center_short_number` | Text, 4,499 % leer | Kostenstellenschlüssel vermutet |
| `Stufe` | `production_stage_code` | Text, 10,355 % leer | Werteliste offen |
| `Stufe Bezeichnung` | `production_stage_name` | Text, 10,355 % leer | Bezeichnung zur Stufe vermutet |

### Qualitätsbefund

- Die Datei ist syntaktisch gut, benötigt aber eine stabile Ereignis-ID.
- **OFFEN:** Beziehung zwischen Produktionszeit und `ZeitmeldungID` in
  `MegenMeldung.csv` bereitstellen; derzeit ist nur die Auftragszuordnung möglich.
- **OFFEN:** 88 fehlende/ungültige Datumswerte fachlich behandeln.

---

## SRC-007 – Mengenmeldungen

### Tabellenbeschreibung

- **Datei:** `MegenMeldung.csv`
- **Hinweis:** Der physische Dateiname wirkt wie ein Schreibfehler; nicht ohne
  Abstimmung umbenennen.
- **Logischer Tabellenname:** `quantity_report`
- **Zeilen:** 198.513
- **Eine Zeile entspricht:** plausibel einer Mengenmeldung; fachlich bestätigen.
- **Primärschlüsselkandidat:** `ZeitmeldungID`, vollständig und eindeutig.
- **Beziehung zum Auftragskopf:** 100 % über `Auftrag Nr`.
- **Exakte doppelte Zeilen:** 0

### Felder

| Physisches Feld | Vorgeschlagener logischer Name | Beobachteter Typ/Vollständigkeit | Rolle und offene Definition |
|---|---|---|---|
| `ZeitmeldungID` | `time_report_id` | ziffernartige ID, eindeutig | Primärschlüsselkandidat; als Text importieren |
| `Auftrag Nr` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |
| `Stück` | `piece_quantity` | numerisch, vollständig | Einheit/Bedeutung offen; 19 Nullwerte |
| `Bogen` | `sheet_quantity` | numerisch, vollständig | Einheit/Bedeutung offen; 47 Nullwerte |
| `Menge` | `reported_quantity` | numerisch, vollständig | Einheit/Abgrenzung offen; 24 Nullwerte |

### Qualitätsbefund

- Schlüssel und Auftragsbeziehung sind technisch gut.
- **OFFEN:** Wie hängt `ZeitmeldungID` mit `ProdZeiten.csv` zusammen?
- **OFFEN:** Sind Stück, Bogen und Menge alternative Einheiten oder gleichzeitig
  gültige Kennzahlen?

---

## SRC-008 – Kostenträgerbuchungen

### Tabellenbeschreibung

- **Datei:** `KTRBuchungenKI.csv`
- **Logischer Tabellenname:** `cost_object_booking`
- **Zeitraum:** 2023-01-20 bis 2026-08-05
- **Zeilen:** 13.787
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
| `BuchungsText` | `booking_text` | Text, 0,044 % leer | Freitext; Vertraulichkeit und Analyseverwendung prüfen |

### Qualitätsbefund

- **OFFEN:** Sind die 23 identischen Zeilen echte Mehrfachbuchungen oder Duplikate?
- **OFFEN:** stabile Buchungs-ID und Kostenartenstamm bereitstellen.

---

## SRC-009 – Rechnungskontrollen

### Tabellenbeschreibung

- **Datei:** `Rechnungskontrollen.csv`
- **Logischer Tabellenname:** `invoice_control_item`
- **Zeitraum:** 2023-01-04 bis 2026-08-05
- **Zeilen:** 9.480
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
| `Firma` | `company_code` | Ganzzahl, konstant | Firmenkontext offen |
| `ReferenzNr` | `reference_number` | ziffernartige ID, vollständig | nicht identisch zu `BelegNummer`; Bedeutung offen |
| `BelegNummer` | `invoice_document_number` | ziffernartige ID, vollständig | Belegbedeutung offen; kein Auftrags-FK |
| `RechnungsDatum` | `invoice_date` | Datum, vollständig | Rechnungsdatum plausibel |
| `GutschriftErzeugen` | `create_credit_note_code` | Ganzzahl, 2 Ausprägungen | Codewerte und Prozesswirkung offen |
| `Lieferant Key` | `supplier_key` | Text, vollständig | Fremdschlüssel zu fehlendem Lieferantenstamm vermutet |
| `Artikel Key` | `invoice_article_key` | Text, vollständig | offenbar anderer Schlüsselraum als Rohwarenartikel |
| `ArtikelGruppe` | `article_group_code` | gemischte ID, vollständig | als Text importieren; 24 Ausprägungen |
| `Bezeichnung` | `description` | Text, vollständig | Freitext/Artikelbezeichnung |
| `Menge` | `invoice_quantity` | Dezimalzahl, vollständig | Einheit/Vorzeichen offen; 145 negative Werte |
| `WarenwertEUR` | `goods_value_eur` | Dezimalzahl, vollständig | EUR laut Name; 145 negative Werte |
| `Traeger` | `order_number` | ziffernartige ID, vollständig | FK zum Auftragskopf bestätigt |

### Qualitätsbefund

- **OFFEN:** Sind 407 identische Zeilen Duplikate oder fachlich zulässige
  Mehrfachpositionen? Ohne Positions-/Buchungs-ID ist dies nicht entscheidbar.
- `ReferenzNr` und `BelegNummer` sind in keiner Zeile identisch; beide Definitionen
  müssen bereitgestellt werden.
- **OFFEN:** Negative Mengen/Werte als Gutschrift oder Storno bestätigen.

---

## Bestätigte und verworfene Beziehungen

| Kind/Feld | Eltern/Feld | Treffer auf Zeilenebene | Bewertung |
|---|---|---:|---|
| Vertriebsposition.`BelegKopfKey` | Auftragskopf.`BelegKopfKey` | 95,053 % | plausibler FK, Exportdifferenz offen |
| Rohwarenposition.`BelegKopf Key` | Auftragskopf.`BelegKopfKey` | 93,993 % | plausibler FK, Exportdifferenz offen |
| Fertigungsmaterial.`Auftrag` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Produktionszeit.`Auftrag` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Mengenmeldung.`Auftrag Nr` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| KTR-Buchung.`KostenTraeger` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| Rechnungskontrolle.`Traeger` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| RW-Buchung.`BelegNummer` | Auftragskopf.`BelegNummer` | 100 % | technisch bestätigt |
| RW-Buchung.`BelegNummer` | Rohwarenposition.`BelegNummer` | 98,470 % | Zuordnung nur auf Auftragsebene |
| RW-Buchung Auftrag + Artikel | Rohwarenposition Auftrag + Artikel | 90,881 % | nicht eindeutig; keine Positionszuordnung |
| Rohwarenposition.`VertriebAuftrag_Pos` | Vertriebsposition.`V_BelegPos_Obj` | 0 % | als direkte Beziehung verworfen |
| Rohwarenposition Kopf + Position | Vertriebsposition Kopf + Position | 0 % | als direkte Beziehung verworfen |
| KTR.`Kostenträger Key` | Auftragskopf-Schlüssel | 0 % | Schlüsselräume verschieden |
| Rechnungskontrolle.`Artikel Key` | Rohwaren-`Artikel Key` | höchstens 1,255 % | vermutlich verschiedene Artikelräume |

## Priorisierte offene Fragen

1. Welcher Auftragskopf-Schlüssel ist dauerhaft und systemübergreifend verbindlich:
   `BelegKopfKey`, `V_BelegKopf_Obj` oder `BelegNummer`?
2. Warum fehlen Auftragsköpfe für 5.346 Vertriebs- und 2.729 Rohwarenpositionen?
3. Welcher Schlüssel verbindet eine Rohwarenposition mit einer Vertriebsposition?
4. Welche eindeutigen Buchungs-/Meldungs-IDs existieren für RW-Buchungen,
   Fertigungsmaterial, Produktionszeiten, KTR-Buchungen und Rechnungskontrollen?
5. Welche Einheiten gelten für alle Mengen-, Dauer-, Bogen-, Stück- und Gewichtsfelder?
6. Welche Währungen, Preisbasen, Rundungen und Vorzeichenregeln gelten?
7. Wie werden Storno, Gutschrift, Rückbuchung und negative Mengen unterschieden?
8. Sind Nullwerte echte Nullmengen/-werte oder Ersatz für fehlende Informationen?
9. Sind die identischen Zeilen in KTR-Buchungen und Rechnungskontrollen zulässig?
10. Warum enthält `RW_Buchungen.csv` ein Buchungsdatum bis 2026-12-23?
11. Welche Wertelisten gelten für Status-, Offen-, Naka-, Kostenart-, Einheiten-
    und Zusatzkostenfelder?
12. Wie hängen `ZeitmeldungID` und Produktionszeiten zusammen?
13. Welche fehlenden Stamm- und Datentabellen werden noch geliefert, insbesondere
    Artikel, Kunde, Lieferant, Vertreter, Kostenstelle und Kostenart?
14. Dürfen Freitextfelder wie `Zusatztext`, `BuchungsText`, `NakaBem` und `Muster`
    für KI-Analysen verwendet werden, oder enthalten sie schützenswerte Inhalte?

## Freigabe

- **Fachlich geprüft durch:** **OFFEN**
- **Technisch geprüft durch:** lokale Strukturprüfung durch Codex; fachliche
  Validierung ausstehend
- **Freigabestatus:** Entwurf
- **Nächste Überprüfung:** nach Beantwortung der priorisierten offenen Fragen oder
  Lieferung weiterer Tabellen
