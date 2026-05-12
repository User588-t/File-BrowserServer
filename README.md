# Mediathek – Lokaler Datei-Server

Ein leichtgewichtiger Web-Server für das lokale Netzwerk (kein Internet nötig).  
Ermöglicht das Durchsuchen, Abspielen und Herunterladen von Dateien über den Browser —  
ideal für Musik, Fotos, Videos und Dokumente vom alten Laptop ins Heimnetz.

---

## Funktionen

| Funktion | Beschreibung |
|---|---|
| 📂 Datei-Browser | Ordner durchsuchen, Navigation mit Breadcrumb |
| 🎵 Music Player | Audio direkt im Browser abspielen (MP3, FLAC, WAV, OGG …) |
| 🖼 Foto-Vorschau | Lightbox beim Klick auf Bilder (JPG, PNG, GIF, WEBP …) |
| 🎬 Video | Video öffnet im neuen Tab |
| ☑ Auswahl | Mehrere Dateien per Checkbox wählen und herunterladen |
| ➕ Mehr laden | Dateien werden in 20er-Batches geladen (kein Lag bei vielen Dateien) |
| 🛡 Admin-Panel | Besucher-Übersicht mit IP, Gerät, Besuchsanzahl, Seiten |
| 📱 Mobil-freundlich | Optimiert für Smartphones (QR-Code Besucher) |

---

## Voraussetzungen

- Python 3.9 oder neuer
- pip

```powershell
python --version   # mindestens 3.9
```

---

## Installation

### 1. Repository herunterladen / Dateien kopieren

```
Explrer Test/
├── main.py
├── requirements.txt
├── templates/
│   ├── index.html
│   └── admin.html
└── visitors.db        ← wird automatisch erstellt
```

### 2. Abhängigkeiten installieren

```powershell
pip install -r requirements.txt
```

Inhalt von `requirements.txt`:
```
flask
```

### 3. Konfiguration anpassen

In `main.py` die folgenden Werte setzen:

```python
ROOT       = Path("Q:/")          # Pfad zum freigegebenen Verzeichnis
ADMIN_PASS = "admin123"           # Admin-Passwort — unbedingt ändern!
ADMIN_PATH = "geheim-admin"       # Geheime URL für das Admin-Panel
```

### 4. Server starten

```powershell
python main.py
```

Server läuft auf Port `8080`. Im Browser öffnen:

```
http://localhost:8080
```

---

## Im lokalen Netzwerk erreichbar machen

### IP-Adresse des Laptops herausfinden

```powershell
ipconfig | findstr "IPv4"
```

Beispiel-Ausgabe: `192.168.1.50`

Dann im Netzwerk erreichbar unter:
```
http://192.168.1.50:8080
```

### Statische IP empfohlen

Damit der QR-Code dauerhaft funktioniert, dem Laptop im Router eine **feste IP per MAC-Bindung** zuweisen (DHCP-Reservation).  
Sonst kann sich die IP nach einem Neustart ändern.

### Windows Firewall — Port freigeben

```powershell
netsh advfirewall firewall add rule `
  name="Mediathek" `
  dir=in action=allow protocol=TCP localport=8080
```

---

## QR-Code erstellen

Die URL `http://192.168.1.50:8080` in einen QR-Generator eingeben, z.B.:
- [qr-code-generator.com](https://www.qr-code-generator.com) (offline-fähig als PNG speichern)
- oder per Python:

```powershell
pip install qrcode[pil]
python -c "import qrcode; qrcode.make('http://192.168.1.50:8080').save('qr.png')"
```

---

## Admin-Panel

Erreichbar unter der geheimen URL:

```
http://192.168.1.50:8080/geheim-admin
```

Login mit dem in `main.py` gesetzten Passwort.

### Was wird angezeigt

| Spalte | Beschreibung |
|---|---|
| Status | Neu / Wiederkehrer |
| IP | IP-Adresse im lokalen Netz |
| Besuche | Wie oft diese Person die Seite geöffnet hat |
| Zuerst gesehen | Erster Besuch (Datum + Uhrzeit) |
| Zuletzt gesehen | Letzter Besuch |
| Seiten | Welche Ordner/Seiten wurden aufgerufen |
| Browser | User-Agent (Gerät, Browser, OS) |

Besucher können einzeln gelöscht werden.

### Wie Besucher erkannt werden

Beim ersten Besuch wird im Browser eine zufällige **UUID** generiert und in `localStorage` gespeichert.  
Diese ID wird bei jedem Seitenaufruf an den Server gesendet.  
So werden wiederkehrende Besucher erkannt — auch wenn die IP wechselt.

> **Hinweis:** Wer `localStorage` löscht (Browser-Daten löschen), gilt beim nächsten Besuch als neu.

---

## Datei-Typen

| Typ | Erweiterungen | Verhalten |
|---|---|---|
| Audio | mp3, wav, flac, ogg, m4a, aac, wma | Player unten im Browser |
| Bild | jpg, jpeg, png, gif, webp, bmp, svg | Lightbox-Vorschau |
| Video | mp4, webm, mkv, mov, avi | Öffnet im neuen Tab |
| Sonstige | alles andere | Nur Download |

---

## Autostart (optional)

### Windows — beim Systemstart automatisch starten

Eine Datei `start.bat` erstellen:

```bat
@echo off
cd /d "C:\Pfad\zum\Explrer Test"
python main.py
```

Diese Datei in den Autostart-Ordner legen:
```
Win + R → shell:startup → start.bat hineinkopieren
```

---

## Projektstruktur

```
Explrer Test/
├── main.py              Server-Code (Flask), alle Routen und Logik
├── requirements.txt     Python-Abhängigkeiten
├── visitors.db          SQLite-Datenbank (automatisch erstellt)
├── README.md            Diese Datei
└── templates/
    ├── index.html       Datei-Browser UI (inkl. Player, Lightbox, Checkboxen)
    └── admin.html       Admin-Panel (Login, Besucher-Tabelle)
```

---

## Technologien

| Was | Womit |
|---|---|
| Server | Python + Flask |
| Datenbank | SQLite (eingebaut in Python, keine Installation nötig) |
| Frontend | Vanilla HTML/CSS/JavaScript (keine externen Libraries) |
| Audio/Video | HTML5 `<audio>` / `<video>` |
| Besucher-ID | `crypto.randomUUID()` + `localStorage` |
