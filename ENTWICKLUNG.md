# Weiterentwicklung & Ideen

Sammlung von möglichen Erweiterungen — nach Themen geordnet.  
Keine feste Reihenfolge, einfach zum Nachschlagen und Weiterbauen.

---

## Sicherheit

- [ ] **HTTPS** — selbst-signiertes Zertifikat mit `mkcert` oder `certifi`, damit Verbindung verschlüsselt ist
- [ ] **IP-Whitelist** — nur bestimmte IP-Bereiche dürfen zugreifen (z.B. nur `192.168.1.*`)
- [ ] **Rate-Limiting** — zu viele Anfragen von einer IP blockieren (z.B. mit `flask-limiter`)
- [ ] **Admin-Session-Timeout** — automatisch ausloggen nach X Minuten Inaktivität
- [ ] **Passwort-Hash** — Admin-Passwort nicht als Klartext in `main.py` speichern (bcrypt)
- [ ] **Besucher-Blacklist** — einzelne IPs im Admin-Panel sperren

---

## Admin-Panel

- [ ] **Debug-Seite** — Server-Status, Config-Check, DB-Infos, ist `Q:/` erreichbar?
- [ ] **Request-Log** — jede Anfrage mit Timestamp mitloggen (welche Datei wurde geladen)
- [ ] **Download-Statistik** — welche Dateien wurden wie oft heruntergeladen
- [ ] **Besucher-Notizen** — im Admin-Panel Notizen zu einzelnen Besuchern hinterlegen
- [ ] **Export** — Besucher-Daten als CSV exportieren
- [ ] **Live-Ansicht** — wer ist gerade online (Last-Seen < 5 Minuten)
- [ ] **Grafiken** — Besuche pro Tag als Diagramm (z.B. mit Chart.js)
- [ ] **Suche** — Besucher nach IP oder Datum filtern

---

## Datei-Browser

- [ ] **Suche** — Dateinamen-Suche über alle Ordner hinweg
- [ ] **Sortierung** — nach Name, Größe, Datum (umschaltbar)
- [ ] **Listen-Ansicht** — Umschalten zwischen Grid und Liste
- [ ] **Favoriten** — Dateien/Ordner als Favorit markieren (gespeichert in `localStorage`)
- [ ] **Verlauf** — zuletzt geöffnete Dateien anzeigen
- [ ] **Vorschau für PDFs** — PDF direkt im Browser anzeigen statt nur Download
- [ ] **Datei-Info** — beim Hover: Größe, Änderungsdatum, EXIF bei Fotos
- [ ] **Thumbnail-Cache** — verkleinerte Vorschaubilder serverseitig generieren und cachen (Pillow)

---

## Music Player

- [ ] **Playlist** — mehrere Songs in Warteschlange packen
- [ ] **Shuffle / Repeat** — Zufallswiedergabe, Wiederholung
- [ ] **Nächster/Vorheriger Track** — Buttons im Player
- [ ] **Lautstärke merken** — in `localStorage` speichern
- [ ] **Mini-Player** — kompakter Player für mobile Geräte
- [ ] **ID3-Tags lesen** — Künstler und Album-Cover aus der MP3-Datei auslesen und anzeigen (mutagen)

---

## Foto-Galerie

- [ ] **Lightbox Navigation** — mit Pfeilen durch Fotos blättern
- [ ] **Slideshow** — automatische Diashow mit Intervall
- [ ] **EXIF anzeigen** — Kamera, Datum, GPS-Koordinaten aus dem Foto lesen (Pillow)
- [ ] **Galerie-Modus** — separater Vollbild-Modus für Bilder im Ordner

---

## Download

- [ ] **ZIP-Download** — ausgewählte Dateien als ZIP packen und runterladen (serverseitig)
- [ ] **Download-Fortschritt** — Fortschrittsbalken bei großen Dateien
- [ ] **Pause/Resume** — Download-Fortsetzung bei Verbindungsabbruch (HTTP Range Requests — Flask unterstützt das bereits teilweise)

---

## Performance

- [ ] **Thumbnail-Generierung** — Bilder beim ersten Aufruf verkleinern und cachen (Pillow)
- [ ] **Lazy Loading** — Bilder nur laden wenn sie im Viewport sind (bereits teilweise drin)
- [ ] **Pagination serverseitig** — bei sehr großen Ordnern (1000+ Dateien) besser als client-seitiges Verstecken
- [ ] **Gzip-Kompression** — Antworten komprimieren (`flask-compress`)

---

## Bedienung

- [ ] **Tastaturkürzel** — `Space` = Play/Pause, `←/→` = Track wechseln, `F` = Vollbild
- [ ] **Drag & Drop Upload** — Dateien in den Browser ziehen und hochladen (neuer Flask-Endpunkt)
- [ ] **Dark/Light Mode** — Umschalter, gespeichert in `localStorage`
- [ ] **Mehrsprachigkeit** — DE/EN umschaltbar

---

## Infrastruktur

- [ ] **Konfigurationsdatei** — `config.json` oder `.env` statt Werte direkt in `main.py`
- [ ] **Logging** — Server-Logs in Datei schreiben (`logging` Modul)
- [ ] **Autostart als Windows-Dienst** — mit `NSSM` oder `pywin32` als echter Windows-Dienst laufen
- [ ] **Mehrere Verzeichnisse** — nicht nur `Q:/`, sondern mehrere Pfade konfigurierbar
- [ ] **Unit-Tests** — automatische Tests für alle Flask-Routen (`pytest` + `flask.testing`)
- [ ] **Docker** — alles in einem Container verpacken für einfache Portierung

---

## Technologie-Alternativen (falls Flask zu klein wird)

| Szenario | Alternative |
|---|---|
| Mehr gleichzeitige Nutzer | FastAPI + uvicorn (async) |
| Komplexes Frontend | Vue.js oder HTMX |
| Echte Nutzerverwaltung | Django mit Auth-System |
| Sehr große Mediathek | Jellyfin (fertige Open-Source-Lösung) |
