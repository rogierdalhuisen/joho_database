# E-grip & Assuportal Sync Handleiding

## 📊 Overzicht

Je hebt twee sync commands om data binnen te halen:

1. **E-grip Formulieren** → Adviesaanvragen (van website)
2. **Assuportal API** → Relaties, Personen, Contracten (van backoffice)

---

## 🔄 E-grip Sync (Adviesaanvragen)

### Wat doet het?
Haalt ingevulde formulieren op van de website (laatste 24 uur).

### Wanneer draaien?
**Dagelijks** - Anders mis je data! De API geeft alleen de laatste 24 uur.

### Command

```bash
# Ga naar de juiste directory
cd /Users/rogier/dev/joho/database/joho_database/src

# Activeer virtual environment (als je in een nieuwe terminal zit)
source ../.venv/bin/activate

# Draai sync
python manage.py sync_egrip_data --form-id 2
```

### Output

```
============================================================
  E-GRIP FORMULIEREN SYNCHRONISATIE
============================================================

✓ E-grip sync voltooid!
  - Succesvol: 3       ← Nieuwe formulieren
  - Geskipt: 9         ← Al eerder geïmporteerd
  - Fouten: 0          ← Geen problemen
```

### ✅ Checklist
- [ ] Docker compose draait (`docker compose up -d`)
- [ ] `.env` bevat `EGRIP_ENDPOINT` en `EGRIP_BEARER_TOKEN`
- [ ] Draai dit **minimaal 1x per dag**

---

## 🏢 Assuportal Sync (Relaties & Contracten)

### Wat doet het?
Haalt klantgegevens en contracten op uit het backoffice systeem.

### Wanneer draaien?
**Wekelijks** of als je weet dat er nieuwe klanten zijn toegevoegd.

### Commands

```bash
cd /Users/rogier/dev/joho/database/joho_database/src
source ../.venv/bin/activate

# Alleen relaties syncen (snel)
python manage.py sync_assuportal_data --relaties-only

# Alleen contracten syncen
python manage.py sync_assuportal_data --contracten-only

# Alles syncen (duurt langer)
python manage.py sync_assuportal_data --all

# Met volledige personen details (langzaam!)
python manage.py sync_assuportal_data --relaties-only --use-detail

# 🆕 Met datum filter (alleen wijzigingen in bepaalde periode)
python manage.py sync_assuportal_data --all --datum-van 2015-11-11 --datum-tot 2015-11-12

# Incrementele sync: alleen laatste 7 dagen
python manage.py sync_assuportal_data --all --datum-van 2025-01-07 --datum-tot 2025-01-14
```

### Output

```
✓ Relaties sync voltooid: 150 succesvol, 0 fouten
✓ Contracten sync voltooid: 300 succesvol, 2 fouten, 5 geskipt
```

### ✅ Checklist
- [ ] Docker compose draait
- [ ] `.env` bevat `ASSUPORTAL_RELATIES`, `ASSUPORTAL_CONTRACTEN`, `ASSUPORTAL_API_TOKEN`
- [ ] Test eerst met `--max-pages 1` bij grote syncs

### 🎯 Datum Filters (Nieuw!)

Je kunt nu specifieke datumperiodes syncen. De API geeft alle records die **aangemaakt of gewijzigd** zijn in die periode.

**Gebruik cases:**
- **Eerste sync**: Alles importeren zonder filter
- **Dagelijkse updates**: `--datum-van [gisteren] --datum-tot [vandaag]`
- **Specifieke periode debuggen**: `--datum-van 2015-11-11 --datum-tot 2015-11-12`

**Formaat:** Altijd `YYYY-MM-DD` (bijvoorbeeld: `2025-01-14`)

---

## 🔗 Hoe Werkt de Koppeling?

### E-grip → Assuportal Merge

Wanneer je **eerst E-grip** draait, dan **daarna Assuportal**:

```
1. E-grip: Formulier komt binnen met email "jan@example.com"
   → Maakt Relatie aan (relatie_id=NULL, source='adviesaanvraag')

2. Assuportal: Relatie "Jan Jansen" met email "jan@example.com" komt binnen
   → Vindt bestaande Relatie met dit email
   → MERGE: Update Relatie (relatie_id=12345, source='api')

✓ Nu is het formulier gekoppeld aan de echte klant!
```

### Aanbevolen Volgorde

```bash
# Stap 1: Haal nieuwe formulieren op
python manage.py sync_egrip_data --form-id 2

# Stap 2: Sync Assuportal (om formulieren te matchen)
python manage.py sync_assuportal_data --relaties-only
```

---

## 📅 Aanbevolen Schema

### Dagelijks (Ochtend)
```bash
python manage.py sync_egrip_data --form-id 2
```

### Wekelijks (Maandag)
```bash
# Optie 1: Volledige sync (alles)
python manage.py sync_assuportal_data --all

# Optie 2: Incrementele sync (alleen laatste week)
# Vervang datum door 7 dagen geleden en vandaag
python manage.py sync_assuportal_data --all --datum-van 2025-01-07 --datum-tot 2025-01-14
```

---

## 🐛 Troubleshooting

### "EGRIP_ENDPOINT not found"
→ Check `.env` file, herstart terminal

### "No such file or directory"
→ Je zit in verkeerde directory, doe `cd src` eerst

### "docker compose connection refused"
→ Start docker: `docker compose up -d`

### "Veel fouten bij sync"
→ Check logs:
```bash
# Bekijk sync logs
tail -n 100 logs/sync.log

# Zoek naar warnings
grep WARNING logs/sync.log

# Zoek naar fouten
grep ERROR logs/sync.log
```

---

## 📊 Data Checken

Na sync, check in Django shell:

```bash
python manage.py shell
```

```python
from comparator_app.models import AdviesAanvragen, Relaties, Contracten

# Check aantallen
print(f"Adviesaanvragen: {AdviesAanvragen.objects.count()}")
print(f"Relaties: {Relaties.objects.count()}")
print(f"Contracten: {Contracten.objects.count()}")

# Check laatste import
laatste = AdviesAanvragen.objects.latest('ingediend_op')
print(f"Laatste aanvraag: {laatste.email} op {laatste.ingediend_op}")
```

---

## 💡 Tips

1. **Maak een alias** in je `~/.zshrc` of `~/.bashrc`:
   ```bash
   alias sync-egrip="cd ~/dev/joho/database/joho_database/src && source ../.venv/bin/activate && python manage.py sync_egrip_data --form-id 2"
   alias sync-assu="cd ~/dev/joho/database/joho_database/src && source ../.venv/bin/activate && python manage.py sync_assuportal_data --all"
   ```

   Dan kun je gewoon typen: `sync-egrip` ✨

2. **Zet reminder** op je telefoon om dagelijks te syncen

3. **Check Metabase** na sync om te zien of data binnenkomt

---

**Vragen? Check de code in:**
- `src/comparator_app/api_egrip.py`
- `src/comparator_app/api_assuportal.py`
