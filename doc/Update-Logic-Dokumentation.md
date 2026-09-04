# KornSW WordPress GitHub AutoUpdate Repository-Template

## Vollständige technische Dokumentation / Agent-Handover

**Stand:** 2026-09-04\
**Status:** Implementiertes und erstmals auf GitHub Actions getestetes
Repository-Template; beim ersten Live-Lauf wurde ein Fehler im
Commit-Schritt gefunden (`git add -A ':!dist'` in Kombination mit
ignoriertem `dist/`). Der festgelegte Fix lautet `git add -A`. Die
nachfolgenden Release-Schritte (Tag-Push, GitHub Release, finaler Push
nach `master`) sind deshalb im ersten Live-Lauf noch nicht praktisch
verifiziert worden.

------------------------------------------------------------------------

# 1. Zweck und Zielbild

Dieses Projekt standardisiert die Veröffentlichung und
Selbstaktualisierung eigener WordPress-Plugins vollständig über GitHub.

Das zentrale Ziel ist **nicht**, ein einzelnes Plugin mit einer
Update-Logik auszustatten. Stattdessen soll ein vorbereitetes
Git-Repository als generisches Template dienen. In dieses Repository
kann ein weitgehend beliebiges, bisher überhaupt nicht für Self-Updates
vorbereitetes WordPress-Plugin gelegt werden. Beim ersten Release-Lauf
erkennt die Pipeline das Plugin, ergänzt die benötigte
Update-Infrastruktur, erzeugt alle Versionierungs- und
Distributionsartefakte on demand und veröffentlicht ein
WordPress-kompatibles ZIP als GitHub Release Asset.

Danach ist das Plugin über die normale WordPress-Update-Infrastruktur
aktualisierbar.

Der gewünschte Komfortablauf lautet:

1.  Repository-Template bereitstellen.
2.  Unvorbereitetes WordPress-Plugin in Repository-Root oder genau eine
    Verzeichnisebene darunter kopieren.
3.  Commit auf `master`.
4.  Push nach GitHub.
5.  GitHub Actions erkennt das Plugin.
6.  Fehlende Versionierungsartefakte werden idempotent erzeugt.
7.  Die bestehende KornSW-Self-Update-Komponente wird in das Plugin
    übernommen.
8.  Plugin-Header werden materialisiert.
9.  Version wird automatisch berechnet.
10. Ein korrekt strukturiertes WordPress-ZIP wird gebaut.
11. Ein Git-Tag und GitHub Release werden erzeugt.
12. Das selbst gebaute ZIP wird als Release Asset hochgeladen.
13. Der materialisierte Repository-Zustand wird mit einem technischen
    `VERSIONING [skip ci]`-Commit nach `master` zurückgeschrieben.
14. WordPress kann `doc/update.json` über GitHub Raw abrufen und bei
    einer neueren Version das Release-ZIP installieren.

GitHub ersetzt damit den früheren eigenen Update-Server vollständig.

------------------------------------------------------------------------

# 2. Verbindliche Grundentscheidungen

## 2.1 Hauptbranch

Für alle KornSW-Repository- und Softwarearbeiten ist der Hauptbranch
standardmäßig:

`master`

Nicht `main`.

Alle URLs, Workflows und Release-Abläufe dieses Templates müssen deshalb
`master` verwenden.

Beispiel:

`https://raw.githubusercontent.com/OWNER/REPOSITORY/master/doc/update.json`

## 2.2 GitHub ist die einzige Distributionsinfrastruktur

Es gibt keinen eigenen Update-Webserver und keine Datenbank für
Plugin-Releases.

Verwendet werden:

-   GitHub Repository für Source und persistierten Versionszustand
-   GitHub Raw für `doc/update.json`
-   Git Tags für Releases und Git-Historiengrenzen
-   GitHub Releases für veröffentlichte Versionen
-   explizit selbst gebaute ZIP-Dateien als GitHub Release Assets
-   GitHub Actions für Versionierung, Materialisierung, Build und
    Veröffentlichung

Die WordPress-Runtime benötigt **keine GitHub API** und **keinen GitHub
Token**.

Für diesen tokenlosen Mechanismus wird zunächst von **öffentlichen
GitHub-Repositories** ausgegangen.

Private Repositories sind ein separater Anwendungsfall, weil Raw- und
Release-Downloads dort Authentifizierung benötigen.

## 2.3 Keine GitHub-"Source code"-Archive als Plugin-Paket

Die automatisch von GitHub erzeugten Assets

-   `Source code (zip)`
-   `Source code (tar.gz)`

dürfen **nicht** als WordPress-Update-Paket verwendet werden.

Die Pipeline baut selbst ein ZIP mit stabiler WordPress-Struktur.

Beispiel:

``` text
hello-world-plugin.zip
└── hello-world-plugin/
    ├── hello-world-plugin.php
    └── self-update.php
```

Genau ein Top-Level-Verzeichnis entspricht dem Plugin-Slug.

------------------------------------------------------------------------

# 3. Versionierung: fachlicher Vertrag

Die Versionierungslogik folgt dem separaten normativen Dokument **AI
Skill KVU - Versioning Rules v1.1**.

Die wichtigsten für dieses Repository relevanten Regeln sind:

-   `doc/changelog.md` ist die führende persistente Release-Datenbank
    und Source of Truth.
-   Entwickler beschreiben Änderungen; die Version wird automatisch
    berechnet.
-   `doc/versioninfo.json` ist ein vollständig materialisierter
    strukturierter Snapshot desselben Versionierungslaufs, aber **keine
    konkurrierende Source of Truth**.
-   `doc/update.json` ist ein WordPress-/GitHub-spezifisches
    Distributionsartefakt und darf ebenfalls niemals zur Berechnung der
    nächsten Version verwendet werden.
-   Normale Änderungen sind standardmäßig PATCH.
-   `**New Feature:**` bewirkt MINOR.
-   `**Breaking Change:**` bewirkt ab 1.x MAJOR; während 0.x MINOR.
-   `**MVP**` erzwingt während 0.x den Übergang auf 1.0.0.
-   Bei mehreren Änderungen gewinnt der höchste Impact.
-   Wenn `Upcoming Changes` leer ist, werden Git-Commit-Subjects als
    Fallback verwendet.
-   Technische Commits mit `VERSIONING` werden vom Git-Fallback
    ignoriert.
-   `[skip ci]` wird aus importierten Commit-Subjects entfernt.
-   Automatische Rückschreib-Commits müssen einen wirksamen CI-Skip
    enthalten.

Der gewünschte technische Commit hat ausdrücklich die Form:

``` text
<identische Meldung des vorherigen fachlichen Commits> -> VERSIONING [skip ci]
```

Beispiel:

``` text
Changed Hello World text -> VERSIONING [skip ci]
```

Nicht gewünscht ist eine generische Message wie:

``` text
VERSIONING: materialize version 0.1.1 [skip ci]
```

------------------------------------------------------------------------

# 4. Repository-Ausgangszustand

Das Repository-Template wurde absichtlich so konzipiert, dass der erste
Release-Lauf den Bootstrap demonstriert.

Gewünschter initialer Zustand:

``` text
repository/
├── .git/
├── .github/
│   └── workflows/
│       └── release.yml
├── .kvu/
│   ├── release.py
│   └── templates/
│       └── self-update.php
├── .gitignore
├── README.md
└── hello-world-plugin/
    └── hello-world-plugin.php
```

Bewusst **nicht vorhanden**:

``` text
doc/
hello-world-plugin/self-update.php
Plugin URI
Update URI
SELF-UPDATE-Bootstrap
versioninfo.json
update.json
Release-ZIP
Git-Tag
```

Das Git-Repository ist bereits mit `master` initialisiert, besitzt im
gelieferten Template aber bewusst noch keinen Commit.

Dadurch soll der erste vom Benutzer angelegte Commit tatsächlich der
Bootstrap-Input sein.

------------------------------------------------------------------------

# 5. Demo-Plugin

Das mitgelieferte Demo-Plugin liegt absichtlich genau eine Ebene
unterhalb des Repository-Roots:

``` text
hello-world-plugin/
└── hello-world-plugin.php
```

Es ist initial ein normales WordPress-Plugin ohne
Self-Update-Infrastruktur.

Der Header enthält initial sinngemäß:

``` php
/**
 * Plugin Name: Hello World Plugin
 * Description: Minimales Demo-Plugin zum Testen der vollautomatischen GitHub-Update-Nachrüstung.
 * Version: 0.0.0
 * Author: KornSW
 * Requires at least: 6.0
 * Requires PHP: 7.4
 */
```

Insbesondere fehlen initial:

``` text
Plugin URI:
Update URI:
```

Außerdem fehlen:

``` text
self-update.php
tk_self_update_bootstrap(...)
```

Das ist beabsichtigt.

------------------------------------------------------------------------

# 6. Automatische Erkennung der WordPress-Entry-Datei

Die Pipeline soll ein Plugin automatisch erkennen können, ohne dass
jedes Repository manuell konfiguriert werden muss.

## 6.1 Erlaubte Suchtiefe

Es werden ausschließlich PHP-Dateien geprüft:

``` text
./*.php
./*/*.php
```

Das bedeutet:

-   Plugin-Entry direkt im Repository-Root: erlaubt
-   Plugin-Entry genau eine Verzeichnisebene darunter: erlaubt
-   tiefere Strukturen werden nicht automatisch erraten

Beispiele:

``` text
repository/plugin.php
```

ist erlaubt.

Ebenso:

``` text
repository/my-plugin/my-plugin.php
```

ist erlaubt.

Nicht automatisch gesucht wird beispielsweise:

``` text
repository/src/plugins/my-plugin/my-plugin.php
```

## 6.2 Erkennungskriterium

Eine PHP-Datei gilt als WordPress-Plugin-Entry, wenn sie einen
WordPress-Plugin-Header mit mindestens

``` text
Plugin Name:
```

enthält.

## 6.3 Eindeutigkeit

Es gelten drei Fälle:

### Kein Treffer

Workflow bricht mit verständlicher Fehlermeldung ab.

### Genau ein Treffer

Diese Datei wird automatisch als Plugin-Entry verwendet.

### Mehrere Treffer

Die Pipeline rät nicht anhand von Dateinamen oder Verzeichnisnamen.

Stattdessen wird abgebrochen und auf den optionalen Marker verwiesen.

## 6.4 Optionaler Entry-Marker

Nur bei Mehrdeutigkeit kann verwendet werden:

``` text
doc/plugin-entry.txt
```

Inhalt ist genau ein relativer Pfad, beispielsweise:

``` text
hello-world-plugin/hello-world-plugin.php
```

Dieser Marker wird **nicht prophylaktisch erzeugt**.

Solange das Repository eindeutig ist, bleibt es ohne zusätzliche
Konfiguration.

------------------------------------------------------------------------

# 7. On-Demand-Erzeugung des `doc/`-Verzeichnisses

Das initiale Template enthält bewusst **keinen `doc/`-Ordner**.

Beim ersten erfolgreichen Versionierungslauf wird dieser erzeugt.

Danach enthält er mindestens:

``` text
doc/
├── changelog.md
├── versioninfo.json
└── update.json
```

Diese Dateien haben unterschiedliche Verantwortlichkeiten.

------------------------------------------------------------------------

# 8. `doc/changelog.md`

## 8.1 Rolle

`changelog.md` ist die führende Versionierungsquelle.

## 8.2 On-Demand-Initialisierung

Fehlt die Datei, erzeugt die Pipeline zunächst eine kanonische
Minimalstruktur:

``` markdown
# Change log

## Upcoming Changes

*(none)*
```

Anschließend kann im **selben Versionierungslauf** bereits der
Git-Fallback greifen.

Beispiel:

Erster Commit:

``` text
Initial Hello World plugin
```

Da `Upcoming Changes` leer ist, wird der Commit-Subject als Änderung
verwendet.

Der erste normale Release von 0.0.0 wird mindestens 0.1.0.

Materialisiertes Ergebnis:

``` markdown
# Change log

## Upcoming Changes

*(none)*

## v 0.1.0
released **2026-09-04**, including:
 - Initial Hello World plugin
```

## 8.3 Manuelle Changes

Später kann der Entwickler unter `Upcoming Changes` explizite Einträge
hinterlegen.

Beispiel:

``` markdown
## Upcoming Changes

- Changed export formatting
- **New Feature:** Added CSV filtering
```

Dann wird kein Git-Fallback benötigt.

------------------------------------------------------------------------

# 9. `doc/versioninfo.json`

`versioninfo.json` ist der generische, maschinenlesbare Snapshot des
aktuellen Versionierungslaufs.

Beispiel:

``` json
{
  "currentVersionWithSuffix": "0.1.0",
  "releaseType": "",
  "currentVersion": "0.1.0",
  "currentMajor": 0,
  "currentMinor": 1,
  "currentFix": 0,
  "previousVersion": "0.0.0",
  "changeGrade": "initial",
  "versionTimeInfo": "14:37:52",
  "versionDateInfo": "2026-09-04",
  "versionNotes": "- Initial Hello World plugin\n"
}
```

Wichtige Konvention:

``` text
currentFix
```

nicht:

``` text
currentPatch
```

`versioninfo.json` wird überschrieben und repräsentiert den aktuellen
Snapshot. Die historische Release-Datenbank bleibt `changelog.md`.

------------------------------------------------------------------------

# 10. `doc/update.json`

## 10.1 Rolle

`update.json` ist das WordPress-/GitHub-spezifische
Runtime-Metadatenformat.

Es wird von der installierten `self-update.php` über HTTP gelesen.

Die Datei ist **keine Source of Truth für Versionierung**.

## 10.2 URL

Die Pipeline setzt als `Update URI` automatisch:

``` text
https://raw.githubusercontent.com/OWNER/REPOSITORY/master/doc/update.json
```

OWNER und REPOSITORY werden aus der GitHub-Actions-Umgebung ermittelt.

Es ist keine manuelle Repository-Konfiguration im Plugin notwendig.

## 10.3 Inhalt

Beispiel:

``` json
{
  "name": "Hello World Plugin",
  "version": "0.1.1",
  "author": "KornSW",
  "homepage": "https://github.com/OWNER/REPOSITORY",
  "download_url": "https://github.com/OWNER/REPOSITORY/releases/download/v0.1.1/hello-world-plugin.zip",
  "requires": "6.0",
  "requires_php": "7.4",
  "tested": "",
  "sections": {
    "description": "Minimales Demo-Plugin ...",
    "changelog": "<h4>Version 0.1.1</h4><ul><li>Changed Hello World text</li></ul>"
  }
}
```

------------------------------------------------------------------------

# 11. Übernahme des aktuellen Changelogs nach WordPress

WordPress soll dem Administrator anzeigen können, was sich bei einem
angebotenen Update geändert hat.

Die bestehende `self-update.php` unterstützt dies bereits über
`plugins_api`.

Sie übernimmt:

``` php
$remote['sections']['changelog']
```

und stellt diesen Wert als:

``` php
$info->sections['changelog']
```

bereit.

Die Pipeline erzeugt deshalb in `update.json` automatisch einen
HTML-Changelog aus **genau dem Change-Set des aktuellen Releases**.

Es wird bewusst nicht die vollständige historische `changelog.md` in
`update.json` kopiert.

Ziel ist die Frage:

> Was ändert sich bei genau diesem Update?

Die vollständige Historie bleibt im Git-Repository in
`doc/changelog.md`.

------------------------------------------------------------------------

# 12. Repository-Metadaten im installierten Plugin

Die Pipeline setzt automatisch:

``` text
Plugin URI: https://github.com/OWNER/REPOSITORY
```

und:

``` text
Update URI: https://raw.githubusercontent.com/OWNER/REPOSITORY/master/doc/update.json
```

Dadurch kennt das installierte Plugin sowohl:

-   sein führendes GitHub-Repository
-   seine Update-Metadatenquelle

Zusätzlich wurde die gemeinsame `self-update.php` um `plugin_row_meta`
ergänzt.

Wenn `Plugin URI` auf `github.com` zeigt, erscheint in der
WordPress-Plugin-Liste ein zusätzlicher Link:

``` text
GitHub Repository
```

Dieser öffnet das jeweilige Repository.

------------------------------------------------------------------------

# 13. Bestehende KornSW-Self-Update-Integration

Die Integration wurde nicht neu erfunden.

Der bestehende, bereits in anderen KornSW-Plugins verwendete Block
bleibt **wortgleich**:

``` php
/*************** SELF-UPDATE ***************/
require_once __DIR__ . '/self-update.php';
tk_self_update_bootstrap( __FILE__ );
/*******************************************/
```

Diese Form ist verbindlich.

Es soll kein neuer KVU-Marker oder alternatives Bootstrap-Schema
eingeführt werden.

------------------------------------------------------------------------

# 14. `self-update.php`

## 14.1 Herkunft

Die Datei basiert auf der bereits bestehenden
KornSW-Self-Update-Implementierung.

Sie ist ausdrücklich so konstruiert, dass sie in mehreren Plugins
gleichzeitig vorhanden sein darf.

Sie schützt globale Definitionen unter anderem über:

``` php
function_exists( 'tk_self_update_bootstrap' )
```

und:

``` php
class_exists( 'TK_Self_Update', false )
```

Trotz gemeinsam geladener Klasse erhält jedes Plugin über:

``` php
tk_self_update_bootstrap( __FILE__ );
```

eine eigene Updater-Instanz.

## 14.2 Zentrale Architekturentscheidung

`self-update.php` selbst enthält **keine repository-spezifische URL**.

Das ist bewusst so.

Die Runtime liest ihre Metadatenquelle aus dem WordPress-Header:

``` text
Update URI:
```

Damit kann die Template-Datei für alle Plugins identisch bleiben.

## 14.3 Template-Masterkopie

Die zentrale Pipeline-Kopie liegt unter:

``` text
.kvu/templates/self-update.php
```

Beim Release wird sie in das tatsächliche Plugin-Verzeichnis kopiert:

``` text
<plugin-root>/self-update.php
```

Die Runtime-Datei wird bei jedem Release aus dem Template
synchronisiert.

Vorteil:

Wenn die gemeinsame Self-Update-Implementierung später verbessert wird,
muss nur die Template-Datei geändert werden. Beim nächsten Release
übernimmt jedes Plugin automatisch den aktuellen Stand.

## 14.4 Relevante WordPress-Hooks

Die bestehende Implementierung verwendet insbesondere:

``` text
update_plugins_<host>
plugins_api
pre_set_site_transient_update_plugins
plugin_row_meta
```

`plugin_row_meta` wurde für den GitHub-Repository-Link ergänzt.

------------------------------------------------------------------------

# 15. Idempotente Injection

Beim ersten Lauf prüft die Pipeline, ob die Plugin-Hauptdatei bereits
enthält:

``` php
tk_self_update_bootstrap( __FILE__ );
```

Fehlt dies, wird der exakte SELF-UPDATE-Block eingefügt.

Bevorzugte Position ist direkt nach einem üblichen ABSPATH-Guard:

``` php
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

/*************** SELF-UPDATE ***************/
require_once __DIR__ . '/self-update.php';
tk_self_update_bootstrap( __FILE__ );
/*******************************************/
```

Existiert der Bootstrap bereits, wird er nicht nochmals eingefügt.

Damit ist die Operation idempotent.

Die `self-update.php` selbst wird dagegen bewusst aus der
Template-Masterkopie synchronisiert.

------------------------------------------------------------------------

# 16. Automatisches Patchen des Plugin-Headers

Die Pipeline materialisiert mindestens:

``` text
Version:
Plugin URI:
Update URI:
```

## Version

Wird aus dem Versionierungslauf gesetzt.

## Plugin URI

Wird auf das aktuelle Repository gesetzt:

``` text
https://github.com/OWNER/REPOSITORY
```

## Update URI

Wird auf das Raw-`update.json` gesetzt:

``` text
https://raw.githubusercontent.com/OWNER/REPOSITORY/master/doc/update.json
```

Dadurch ist ein neu eingebrachtes Plugin nach dem ersten erfolgreichen
Release selbstupdatefähig.

------------------------------------------------------------------------

# 17. Git-Fallback

Wenn `Upcoming Changes` keine manuellen Changes enthält, wird die
Git-Historie verwendet.

Es werden Commit-Subjects importiert.

Technische Versionierungscommits mit `VERSIONING` werden ignoriert.

CI-Skip-Marker werden aus importierten Subjects entfernt.

Die Anzahl der importierten Fallback-Commits ist begrenzt.

Eine geeignete gemergte Versionstag-Grenze wird bevorzugt als
Historiengrenze verwendet.

Wenn weder manuelle Changes noch brauchbare Git-Changes vorliegen, wird
als definierter Fallback verwendet:

``` text
New revision without significant changes
```

------------------------------------------------------------------------

# 18. Release-ZIP

## 18.1 Zielstruktur

Das ZIP muss WordPress-kompatibel sein.

Bei:

``` text
repository/
└── hello-world-plugin/
    ├── hello-world-plugin.php
    └── self-update.php
```

entsteht:

``` text
hello-world-plugin.zip
└── hello-world-plugin/
    ├── hello-world-plugin.php
    └── self-update.php
```

## 18.2 Warum dies wichtig ist

Frühere AutoUpdate-Arbeiten zeigten, dass falsche ZIP-Strukturen dazu
führen können, dass WordPress das Plugin in ein neues/verändertes
Verzeichnis installiert und anschließend das bisherige Plugin als nicht
mehr vorhanden betrachtet.

Deshalb gilt:

-   stabiler Plugin-Slug
-   genau ein Top-Level-Verzeichnis
-   Hauptdatei darunter
-   kein zufälliger GitHub-Source-Archiv-Verzeichnisname

## 18.3 Nicht in Release-ZIP übernehmen

Repository-Infrastruktur gehört nicht in das WordPress-Plugin-ZIP.

Dazu zählen insbesondere:

``` text
.git/
.github/
.kvu/
doc/
dist/
```

wenn das Plugin in einem eigenen Unterordner liegt.

------------------------------------------------------------------------

# 19. Release-Reihenfolge und Race-Condition-Schutz

Ein wichtiger Designpunkt ist die Reihenfolge der Veröffentlichung.

Naiv wäre:

1.  `update.json` nach `master` pushen.
2.  Release erzeugen.
3.  ZIP hochladen.

Das ist falsch, weil WordPress zwischen Schritt 1 und 3 bereits die neue
Version sehen könnte, deren `download_url` noch 404 liefert.

Deshalb gilt die transaktionale Reihenfolge:

``` text
Versionierung
    ↓
Materialisierung lokal
    ↓
ZIP bauen und validieren
    ↓
VERSIONING-Commit lokal erzeugen
    ↓
Tag auf diesen Commit setzen
    ↓
nur Tag pushen
    ↓
GitHub Release erzeugen
    ↓
ZIP als Release Asset hochladen
    ↓
erst danach VERSIONING-Commit nach master pushen
```

Damit wird:

``` text
doc/update.json
```

erst auf `master` sichtbar, wenn das darin referenzierte ZIP bereits als
Release Asset existiert.

Ein Fehler beim letzten `master`-Push ist damit sicherer als die
umgekehrte Reihenfolge:

-   Release existiert eventuell bereits
-   WordPress sieht aber weiterhin die alte `update.json`
-   es wird kein kaputter Download beworben

------------------------------------------------------------------------

# 20. Wichtige Release-Invariante

Für einen erfolgreichen Release soll gelten:

``` text
Tag vX.Y.Z
=
exakter materialisierter Source-Stand
=
Plugin-Header Version X.Y.Z
=
doc/versioninfo.json Version X.Y.Z
=
doc/update.json Version X.Y.Z
=
GitHub Release vX.Y.Z
=
Release Asset für X.Y.Z
```

Diese Konsistenz ist wichtiger als ein möglichst kurzer Workflow.

------------------------------------------------------------------------

# 21. GitHub Actions Workflow

Workflow-Datei:

``` text
.github/workflows/release.yml
```

Trigger:

``` yaml
on:
  push:
    branches:
      - master
  workflow_dispatch:
```

Der normale Entwicklungsmodus ist damit:

``` text
kleine Änderung
→ Commit
→ Push master
→ neuer Release
```

Genau dies ist für das gewünschte Live-Testmodell beabsichtigt.

Auch eine triviale Änderung des Hello-World-Texts soll einen neuen
Release erzeugen.

------------------------------------------------------------------------

# 22. CI-Rekursionsschutz

Der von der Pipeline selbst erzeugte technische Commit darf keinen
weiteren Release auslösen.

Dafür werden zwei Mechanismen kombiniert:

1.  Commit enthält:

``` text
[skip ci]
```

2.  Workflow prüft zusätzlich auf:

``` text
VERSIONING
```

Der technische Commit hat beispielsweise:

``` text
Changed Hello World text -> VERSIONING [skip ci]
```

------------------------------------------------------------------------

# 23. GitHub-Schreibrechte

Der Workflow benötigt:

``` yaml
permissions:
  contents: write
```

Wenn Repository- oder Organisationseinstellungen dies einschränken, muss
unter GitHub geprüft werden:

``` text
Repository
→ Settings
→ Actions
→ General
→ Workflow permissions
```

Dort muss der `GITHUB_TOKEN` Schreibrechte erhalten können.

Für den vorgesehenen Standardfall ist kein separat erzeugter PAT nötig.

------------------------------------------------------------------------

# 24. Der erste Live-Test und gefundener Fehler

Der erste reale GitHub-Actions-Lauf erreichte erfolgreich:

``` text
Set up job
Checkout complete repository history
Set up Python
Configure Git identity
Capture triggering commit subject
Materialize plugin update support and build release
Validate generated state
```

Damit sind insbesondere bereits praktisch bestätigt:

-   Checkout funktioniert
-   Python-Release-Skript läuft auf GitHub
-   Plugin-Erkennung funktioniert
-   Materialisierung funktioniert
-   Build funktioniert
-   Validierung funktioniert

Der Lauf scheiterte erst bei:

``` text
Commit materialized repository state locally
```

## Ursache

Im Workflow stand:

``` bash
git add -A ':!dist'
```

Gleichzeitig enthält `.gitignore`:

``` text
dist/
```

Git brach mit einer Meldung ab, dass `dist` von `.gitignore` ignoriert
werde.

## Festgelegter Fix

Da `dist/` bereits korrekt ignoriert wird, ist das negative Pathspec
überflüssig.

Verbindliche Korrektur:

``` bash
git add -A
```

anstatt:

``` bash
git add -A ':!dist'
```

Damit werden alle materialisierten Repository-Dateien aufgenommen,
während `dist/` weiterhin durch `.gitignore` ausgeschlossen bleibt.

## Konsequenz für den Teststatus

Weil der Fehler vor den folgenden Schritten auftrat, wurden im ersten
Live-Lauf noch nicht praktisch ausgeführt:

``` text
Push release tag first
Publish GitHub Release with custom WordPress ZIP
Expose generated metadata on master last
```

Diese Schritte sind architektonisch implementiert, aber noch durch den
nächsten Live-Test zu verifizieren.

------------------------------------------------------------------------

# 25. Delta-Arbeitsweise für zukünftige Agents

Bei weiteren Änderungen soll **delta-basiert** gearbeitet werden.

Nach einer ausführlichen Erklärung muss jede Antwort am Ende einen
kurzen, unmittelbar ausführbaren Änderungsblock enthalten.

Gewünschtes Format:

``` text
Änderung durchführen

Datei:
.github/workflows/release.yml

Ersetze:

git add -A ':!dist'

durch:

git add -A
```

Bei mehreren notwendigen Deltas können entsprechend mehrere klar
getrennte Datei-/Ersetzen-Blöcke verwendet werden.

Wichtig ist:

-   exakte Datei nennen
-   exakten alten Inhalt nennen
-   exakten neuen Inhalt nennen
-   bei Ergänzungen die Einfügeposition nennen
-   keine vagen Aussagen wie "Workflow entsprechend anpassen"

------------------------------------------------------------------------

# 26. Erwarteter End-to-End-Test

Nach Einbau des bekannten `git add -A`-Fixes:

## Schritt 1: erfolgreichen ersten Release erzeugen

Einen normalen Commit auf `master` pushen.

Erwartet:

-   Workflow erfolgreich
-   `doc/` entsteht
-   `self-update.php` erscheint im Plugin-Verzeichnis
-   SELF-UPDATE-Block erscheint in Hauptdatei
-   `Version:` wird materialisiert
-   `Plugin URI:` wird gesetzt
-   `Update URI:` wird gesetzt
-   `versioninfo.json` entsteht
-   `update.json` entsteht
-   Tag `v0.1.0` oder gemäß tatsächlicher Historie passende Version
    entsteht
-   GitHub Release entsteht
-   eigenes Plugin-ZIP erscheint als Release Asset
-   technischer VERSIONING-Commit wird nach `master` geschrieben

## Schritt 2: Release-ZIP in WordPress installieren

Nur das explizite Release Asset verwenden.

Nicht GitHubs Source-Code-ZIP.

## Schritt 3: kleine Plugin-Änderung

Beispielsweise:

``` text
Hello World!
```

ändern in:

``` text
Hello World Nummer 2!
```

Commit:

``` text
Changed Hello World text
```

Push auf `master`.

Wenn `Upcoming Changes` leer ist, muss Git-Fallback daraus einen
Patch-Release erzeugen.

Beispiel:

``` text
0.1.0 → 0.1.1
```

## Schritt 4: WordPress-Update prüfen

In WordPress:

``` text
Dashboard → Aktualisierungen
```

ggf. erneut prüfen.

Erwartet:

-   neue Plugin-Version wird angeboten
-   Details können angezeigt werden
-   aktueller Changeblock wird im Changelog dargestellt
-   GitHub-Repository ist als Link verfügbar
-   Update installiert das neue Release-ZIP
-   Plugin bleibt unter demselben Plugin-Slug aktiv/installiert
-   neue Hello-World-Ausgabe ist sichtbar

------------------------------------------------------------------------

# 27. Bekannte zukünftige Prüf- und Verbesserungspunkte

Folgende Punkte sind nach dem ersten vollständigen Live-Roundtrip weiter
zu prüfen:

## 27.1 GitHub Release-Schritte

Noch praktisch zu verifizieren:

-   Tag-Push mit `GITHUB_TOKEN`
-   `gh release create`
-   Upload des selbst gebauten ZIPs
-   finaler Push des materialisierten Commits nach `master`

## 27.2 WordPress-Roundtrip

Noch praktisch zu verifizieren:

-   Raw-`update.json` wird zuverlässig von WordPress gelesen
-   Update erscheint im Standard-UI
-   `plugins_api` zeigt Changelog
-   `plugin_row_meta` zeigt GitHub-Link
-   Release-ZIP wird installiert
-   Plugin-Verzeichnis bleibt stabil
-   kein Deaktivierungs-/Pfadproblem

## 27.3 `upgrader_source_selection`

In älteren KornSW-AutoUpdate-Arbeiten war eine defensive Normalisierung
des entpackten Plugin-Verzeichnisses über `upgrader_source_selection`
relevant.

Die aktuell übernommene `self-update.php` enthält diese Normalisierung
nicht.

Da das neue Release-ZIP bereits deterministisch mit exakt dem richtigen
Top-Level-Slug gebaut wird, sollte sie im Normalfall nicht nötig sein.
Beim echten WordPress-Roundtrip muss aber explizit beobachtet werden, ob
WordPress den Pfad stabil behandelt.

Wenn ein Pfadproblem auftritt, soll die bereits bekannte
`upgrader_source_selection`-Strategie wieder ergänzt werden, statt die
ZIP-Struktur aufzuweichen.

## 27.4 Prereleases

Der normative Versionierungsvertrag enthält Prerelease-Semantik.

Das aktuelle Demo-/Template-Ziel konzentriert sich zunächst auf Releases
vom Hauptbranch `master`.

Vor produktiver Nutzung von Feature-Branch-Prereleases muss festgelegt
werden, ob und wie WordPress stabile Installationen solche Prereleases
angeboten bekommen dürfen.

Empfehlung: stabile `update.json` auf `master` sollte standardmäßig nur
den stabilen Kanal bewerben.

## 27.5 `tested`

`Requires at least` und `Requires PHP` können aus dem Plugin-Header
übernommen werden.

Für WordPress `tested` gibt es keinen entsprechenden zwingenden
Standardheader im Demo-Plugin. Der aktuelle Generator kann deshalb einen
leeren Wert erzeugen.

Später kann hierfür eine bewusste Konvention ergänzt werden.

------------------------------------------------------------------------

# 28. Sicherheits- und Robustheitsprinzipien

Die Pipeline soll niemals stillschweigend riskante Annahmen treffen.

Beispiele:

-   mehrere Plugin-Entry-Kandidaten → Fehler statt Raten
-   keine Plugin-Hauptdatei → Fehler
-   ungültiger Marker → Fehler
-   ZIP ohne erwartete Struktur → Fehler
-   fehlende generierte JSON-Datei → Fehler
-   nicht parsebares JSON → Fehler
-   Version im Plugin-Header stimmt nicht mit berechneter Version
    überein → Fehler
-   Release erst bewerben, wenn ZIP existiert

Runtime-seitig gilt:

Wenn `update.json` vorübergehend nicht erreichbar oder ungültig ist,
darf das installierte Plugin nicht beschädigt werden. Es soll dann
schlicht kein Custom-Update angeboten werden.

------------------------------------------------------------------------

# 29. Trennung der Verantwortlichkeiten

Die Architektur soll langfristig diese klare Richtung behalten:

``` text
doc/changelog.md
        │
        ▼
KVU-Versionierung
        │
        ├──────────────► doc/versioninfo.json
        │
        ▼
Release-/WordPress-Materialisierung
        │
        ├──────────────► Plugin-Header
        ├──────────────► self-update.php
        ├──────────────► doc/update.json
        └──────────────► Plugin-ZIP
                              │
                              ▼
                       GitHub Release Asset
```

Wichtig:

-   keine Rückwärtsableitung der Version aus `update.json`
-   keine Rückwärtsableitung aus Plugin-Header, wenn `changelog.md`
    bereits etabliert ist
-   `versioninfo.json` ist Snapshot, nicht Source of Truth
-   Git Tags dienen als Historien-/Release-Hilfe und Konsistenzsignal,
    nicht als Ersatz für die Changelog-Semantik

------------------------------------------------------------------------

# 30. Warum diese Architektur gewählt wurde

Die Architektur verbindet mehrere Ziele:

## Minimaler Plugin-spezifischer Aufwand

Ein Plugin muss nicht manuell für GitHub-AutoUpdate vorbereitet werden.

## Zentrale Wartbarkeit

Die Self-Update-Runtime liegt als gemeinsames Template in
`.kvu/templates/self-update.php`.

## Reproduzierbare Releases

Version, Changelog, JSON-Metadaten, Tag und ZIP werden aus einem
gemeinsamen Versionierungslauf erzeugt.

## Git-native Historie

Der materialisierte Zustand wird in das Repository zurückgeschrieben.

## Kein eigener Server

GitHub übernimmt Source, statische Metadaten und Binärartefakte.

## WordPress-native Bedienung

Der Benutzer erhält Updates über die normale
WordPress-Plugin-Verwaltung.

## Transparenz

Das installierte Plugin verweist direkt auf sein GitHub-Repository und
kann den aktuellen Release-Changelog anzeigen.

------------------------------------------------------------------------

# 31. Verbindliche Konventionen für Weiterentwicklung

Andere Agents sollen folgende Entscheidungen **nicht ohne ausdrückliche
Anforderung ändern**:

1.  Hauptbranch heißt `master`.
2.  `doc/changelog.md` bleibt Source of Truth.
3.  `doc/versioninfo.json` bleibt generischer Snapshot.
4.  `doc/update.json` bleibt WordPress-spezifisches
    Distributionsmetadatum.
5.  `self-update.php` bleibt eine separate Runtime-Datei.
6.  Der SELF-UPDATE-Integrationsblock bleibt wortgleich.
7.  Repository-spezifische URL steht im Plugin-Header `Update URI`,
    nicht hart in `self-update.php`.
8.  `Plugin URI` zeigt auf das GitHub-Repository.
9.  Release-ZIP wird selbst gebaut.
10. GitHub Source-Code-ZIPs werden nicht verwendet.
11. Plugin-Entry wird nur im Root oder genau eine Ebene darunter
    automatisch gesucht.
12. Mehrdeutigkeit führt zu Fehler bzw. optional `doc/plugin-entry.txt`.
13. Fehlende `doc`-Artefakte entstehen on demand.
14. Operationen müssen idempotent sein.
15. `self-update.php` darf aus dem zentralen Template synchronisiert
    werden.
16. `update.json` wird erst auf `master` sichtbar gemacht, nachdem das
    Release Asset existiert.
17. technischer Commit übernimmt den vorherigen Commit-Subject und hängt
    `-> VERSIONING [skip ci]` an.
18. Bei Delta-Arbeit endet die Agent-Antwort mit einer exakten
    Datei-/Ersetzen-Anweisung.

------------------------------------------------------------------------

# 32. Aktueller unmittelbarer nächster Schritt

Im aktuell live getesteten Repository muss der bekannte Workflow-Fehler
korrigiert werden.

## Änderung durchführen

**Datei:**

``` text
.github/workflows/release.yml
```

**Ersetze:**

``` bash
git add -A ':!dist'
```

**durch:**

``` bash
git add -A
```

Danach die Änderung normal committen und nach `master` pushen. Der
nächste Workflow-Lauf dient als erster vollständiger Test von Tag-Push,
GitHub Release, ZIP-Asset und finalem Rückschreib-Commit.

------------------------------------------------------------------------

# 33. Agent-Handover-Kurzfassung

Wenn ein neuer Agent dieses Projekt übernimmt, ist das mentale Modell:

> Dieses Repository ist eine generische GitHub-basierte Release-Maschine
> für WordPress-Plugins. Ein nacktes Plugin im Root oder genau eine
> Ebene darunter wird beim ersten Push automatisch erkannt und mit der
> bestehenden KornSW-`self-update.php` sowie dem exakt bestehenden
> Bootstrap-Block ausgestattet. Versionierung folgt dem
> KVU-v1.1-Contract mit `doc/changelog.md` als Source of Truth.
> `doc/versioninfo.json` und `doc/update.json` entstehen on demand.
> GitHub Raw liefert die Update-Metadaten, ein selbst gebautes GitHub
> Release Asset liefert das WordPress-ZIP. Der materialisierte Zustand
> wird mit `<vorheriger Commit> -> VERSIONING [skip ci]` nach `master`
> zurückgeschrieben. Die Veröffentlichung ist so geordnet, dass
> WordPress niemals absichtlich eine neue `update.json` sieht, bevor das
> zugehörige ZIP existiert. Der erste Live-Test erreichte bereits
> Materialisierung und Validierung; aktuell muss nur der bekannte
> `git add`-Fehler korrigiert und danach der vollständige
> Release-Roundtrip verifiziert werden.
