# KornSW WordPress GitHub AutoUpdate Template

Dieses Repository ist absichtlich im Ausgangszustand **noch nicht materialisiert**.

Insbesondere fehlen vor dem ersten Workflow-Lauf bewusst:

- `doc/`
- `hello-world-plugin/self-update.php`
- `Plugin URI`
- `Update URI`
- der SELF-UPDATE-Bootstrap-Block im Demo-Plugin
- `versioninfo.json`
- `update.json`
- GitHub Release / Tag

Das Demo-Plugin liegt absichtlich eine Ebene unterhalb des Repository-Roots:

`hello-world-plugin/hello-world-plugin.php`

## Erwarteter erster Test

1. Lege ein **öffentliches** GitHub-Repository an.
2. Entpacke dieses ZIP lokal.
3. Setze das Remote:
   `git remote add origin <DEINE-GITHUB-REPOSITORY-URL>`
4. Führe den ersten Commit aus:
   `git add .`
   `git commit -m "Initial Hello World plugin"`
5. Push:
   `git push -u origin master`

Der Push startet `.github/workflows/release.yml`.

## Was beim ersten Lauf on demand entsteht

Die Pipeline:

1. erkennt genau eine WordPress-Plugin-Hauptdatei im Root oder genau eine Ebene darunter;
2. erzeugt `doc/changelog.md`, falls es fehlt;
3. nutzt `Upcoming Changes`, andernfalls Git-Commit-Subjects als Fallback;
4. berechnet die nächste Version;
5. kopiert `.kvu/templates/self-update.php` neben das Plugin;
6. injiziert exakt den bestehenden KornSW-SELF-UPDATE-Block;
7. setzt `Plugin URI` auf das aktuelle GitHub-Repository;
8. setzt `Update URI` auf:
   `https://raw.githubusercontent.com/OWNER/REPOSITORY/master/doc/update.json`
9. setzt den Plugin-Header `Version`;
10. erzeugt `doc/versioninfo.json`;
11. erzeugt `doc/update.json` inklusive aktuellem Changelog-Block;
12. baut ein eigenes WordPress-ZIP mit genau einem Top-Level-Pluginordner;
13. erstellt lokal den technischen Commit:
   `<vorheriger Commit-Subject> -> VERSIONING [skip ci]`;
14. pusht zuerst den Git-Tag;
15. veröffentlicht das GitHub Release inklusive eigenem Plugin-ZIP;
16. pusht erst danach den materialisierten Commit nach `master`.

Dadurch wird die neue `update.json` erst auf `master` sichtbar, wenn das referenzierte Release-Asset bereits existiert.

## Plugin-Erkennung

Automatisch durchsucht werden ausschließlich:

- `./*.php`
- `./*/*.php`

Eine Datei gilt als Plugin-Entry, wenn sie einen WordPress-Header `Plugin Name:` besitzt.

Bei genau einem Treffer wird automatisch fortgefahren.

Bei mehreren Treffern kann optional später diese Datei verwendet werden:

`doc/plugin-entry.txt`

mit genau einem relativen Pfad, z. B.:

`hello-world-plugin/hello-world-plugin.php`

Sie wird **nicht** prophylaktisch angelegt.

## WordPress-Komfortfunktionen

Nach der Materialisierung enthält `doc/update.json` den aktuellen Release-Changeblock unter:

`sections.changelog`

Die vorhandene `self-update.php` liefert ihn an WordPress `plugins_api`, sodass er in den Plugin-Details / Update-Details angezeigt werden kann.

Zusätzlich setzt die Pipeline das Repository als `Plugin URI`.
`self-update.php` ergänzt in der Plugin-Liste einen anklickbaren Link `GitHub Repository`.

## Zweiten Release testen

Nach erfolgreicher Installation von `0.1.0` in WordPress:

1. Ändere in `hello-world-plugin/hello-world-plugin.php` den Text `Hello World!`.
2. Committe z. B.:
   `git commit -am "Changed Hello World text"`
3. `git push`

Wenn `Upcoming Changes` leer ist, wird der Commit-Subject als Change übernommen.
Das ergibt im Normalfall einen Patch-Bump, z. B. `0.1.0 -> 0.1.1`.

## GitHub-Einstellung

Falls der Workflow nicht in das Repository schreiben darf:

Repository → Settings → Actions → General → Workflow permissions

Dort Schreibrechte für `GITHUB_TOKEN` erlauben (`Read and write permissions`).

## Wichtig

- Hauptbranch ist verbindlich `master`.
- Das Repository muss für diesen tokenlosen WordPress-Test öffentlich sein.
- GitHubs automatisch erzeugtes `Source code (zip)` wird nicht als Plugin-Paket verwendet.
- Das Plugin-Paket ist das explizit von `.kvu/release.py` gebaute Release-Asset.
