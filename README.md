# GreenSpace — Dublin Footpaths & Parks Explorer

A Django + PostGIS web app that allows users to explore Dublin’s parks, footpaths, and playgrounds on an interactive Leaflet map.  
It supports:

- Searching for parks and playgrounds
- Finding nearby parks and footpaths within a radius
- Viewing the nearest playground from your location
- Basic CRUD operations (Create, Update, Delete) for playgrounds

---

## Tech Stack

- **Backend:** Django 5 + Django REST Framework
- **Database:** PostgreSQL 16 + PostGIS 3
- **Frontend:** HTML, Bootstrap 5, Leaflet.js
- **Deployment:** Localhost (Docker optional)

---

## Project Structure

greenfinder/
├─ manage.py
├─ requirements.txt
├─ README.md
├─ data/
│ ├─ dcc_parks.geojson
│ ├─ osm_footways.geojson
│ └─ osm_playgrounds.geojson
├─ templates/
│ └─ index.html
├─ static/img/
│ └─ bg-city.jpg
├─ server/
│ ├─ settings.py
│ └─ urls.py
└─ api/
├─ views.py
├─ urls.py
├─ urls_frontend.py
├─ views_frontend.py
└─ management/commands/import_geojson.py

| Feature            | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| 🗺️ Interactive Map | Leaflet-based map centered on Dublin                       |
| 📍 Location        | Use browser location or click map                          |
| 🌳 Parks Nearby    | Fetch parks within a chosen radius                         |
| 🛝 Playgrounds      | Find nearest playground                                    |
| 🚶 Footpaths       | Display routes intersecting parks or within radius         |
| ✏️ Playground CRUD | Create, rename, or delete playgrounds directly from the UI |
| 🧹 Clear Map       | Reset layers or press “Esc”                                |

| Endpoint                       | Method | Description             |
| ------------------------------ | ------ | ----------------------- |
| `/api/parks/within`            | GET    | Parks near a coordinate |
| `/api/routes/within`           | GET    | Routes within radius    |
| `/api/playgrounds/nearest`     | GET    | Find nearest playground |
| `/api/playgrounds`             | POST   | Create new playground   |
| `/api/playgrounds/<id>`        | PATCH  | Update name             |
| `/api/playgrounds/<id>/delete` | DELETE | Delete by ID            |
