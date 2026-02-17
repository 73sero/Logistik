# 🚚 Logistics Backoffice - Setup Guide

## Step-by-Step Installation & Start

### 1️⃣ Repository clonen
```bash
cd /opt  # oder wo du das haben willst
git clone https://github.com/73sero/Logistik.git
cd Logistik
```

### 2️⃣ Python Dependencies installieren
```bash
pip install -r requirements.txt
# Oder mit --break-system-packages wenn nötig:
pip install --break-system-packages -r requirements.txt
```

### 3️⃣ Server starten
```bash
python3 logistik_api.py
```

Du solltest sehen:
```
 * Running on http://127.0.0.1:5000
 * Running on http://[deine-ip]:5000
```

### 4️⃣ Dashboard öffnen
- **Local**: http://localhost:5000
- **Remote**: http://[dein-server-ip]:5000

---

## 📋 Was ist drin?

| Datei | Zweck |
|-------|-------|
| `logistik_api.py` | Flask-Server (Hauptdatei) |
| `logistik_db.py` | Datenbank-API für Agents |
| `logistik.db` | SQLite Datenbank (Sample-Daten) |
| `workflow_engine.py` | Task-Automation (Auto-Agent-Trigger) |
| `agent_prompts.md` | Agent-Verhalten dokumentiert |
| `dashboard/` | Web-UI (HTML/CSS/JS) |
| `START_SYSTEM.py` | Master Orchestrator |

---

## 🎯 Dashboard Features

- **6 Tabs**: Dashboard | Orders | Drivers | Agents | Invoices | Activity Log
- **Real-time Refresh**: Auto-update every 10 seconds
- **Dark Theme**: Green hacker aesthetic (#00ff88)
- **Sample Data**: 2 customers, 3 drivers ready to test

---

## ⚙️ API Konfiguration

Das System nutzt **OpenAI GPT-5.2** als Primary Model. Der API-Key wird von OpenClaw bereitgestellt.

Wenn du den Key wechseln willst:
1. Neue API-Key von https://platform.openai.com/api-keys
2. In `/data/.openclaw/agents/main/agent/auth-profiles.json` setzen

---

## 🚀 Erste Schritte

1. **Server starten**: `python3 logistik_api.py`
2. **Dashboard öffnen**: http://localhost:5000
3. **Test-Order erstellen**: Via Orders-Tab
4. **Activity Log monitoren**: Schau ob Agents automatisch Tasks verarbeiten

---

## 🛠 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install --break-system-packages flask
```

### "Port 5000 already in use"
```bash
# Nimm einen anderen Port:
python3 logistik_api.py --port 5001
```

### Server läuft aber Dashboard zeigt Fehler
- Browser-Cache leeren (Ctrl+Shift+Del)
- Console öffnen (F12) → schaun ob Errors sind
- Logs ansehen: `logistik_api.py` startet mit Debug-Output

---

## 📞 Support

Probleme? Sag Bescheid mit:
- Error-Message (Terminal-Output)
- Was du gerade probiert hast
- Welcher Tab / Action fehlgeschlagen

---

**Viel Erfolg!** 🚀
