from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_http_methods(["POST"])
def playground_create(request):
    """
    JSON body: {"name": "New Playground", "lat": 53.34, "lng": -6.26}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name") or "Playground"
        lat = float(body["lat"])
        lng = float(body["lng"])
    except Exception as e:
        return JsonResponse({"error": f"Invalid body: {e}"}, status=400)

    sql = """
      INSERT INTO playgrounds(name, source, geom)
      VALUES (%s, 'Manual', ST_SetSRID(ST_MakePoint(%s,%s),4326))
      RETURNING id, name, ST_AsGeoJSON(geom) AS geom;
    """
    rows = _fetchall(sql, [name, lng, lat])
    return JsonResponse({"created": rows[0]}, status=201)

@csrf_exempt
@require_http_methods(["PATCH"])
def playground_update(request, pk):
    """
    JSON body: {"name": "New Name"}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name")
        if not name:
            return JsonResponse({"error": "name required"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Invalid body: {e}"}, status=400)

    sql = "UPDATE playgrounds SET name=%s WHERE id=%s RETURNING id, name;"
    rows = _fetchall(sql, [name, pk])
    if not rows:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({"updated": rows[0]})

@csrf_exempt
@require_http_methods(["DELETE"])
def playground_delete(request, pk):
    sql = "DELETE FROM playgrounds WHERE id=%s RETURNING id;"
    rows = _fetchall(sql, [pk])
    if not rows:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({"deleted": rows[0]["id"]})


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})

def _fetchall(sql, params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

@require_GET
def parks_within(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        radius_m = float(request.GET.get('radius_m', '2000'))
    except Exception as e:
        return JsonResponse({"error": f"lat,lng required: {e}"}, status=400)

    sql = """
      SELECT id, name, category, area_ha,
             ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0003)) AS geom
      FROM parks
      WHERE ST_DWithin(
      geography(geom),
      ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,
      %s
    )
    ORDER BY ST_Distance(
      geography(geom),
      ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography
    )
    LIMIT 500;
    """
    rows = _fetchall(sql, [lng, lat, radius_m, lng, lat])
    return JsonResponse({"features": rows})

@require_GET
def playgrounds_nearest(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        limit = int(request.GET.get('limit', '1'))
    except Exception as e:
        return JsonResponse({"error": f"lat,lng required: {e}"}, status=400)

    sql = """
      SELECT id, name, source,
             ST_AsGeoJSON(geom) AS geom,
             ST_Distance(
               geom::geography,
               ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography
             ) AS meters
      FROM playgrounds
      ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s,%s),4326)
      LIMIT %s;
    """
    rows = _fetchall(sql, [lng, lat, lng, lat, limit])
    return JsonResponse({"features": rows})

@require_GET
def routes_intersecting_park(request):
    try:
        park_id = int(request.GET.get('park_id'))
    except Exception:
        return JsonResponse({"error": "park_id required"}, status=400)

    sql = """
      SELECT r.id, r.name, r.source,
             ST_AsGeoJSON(ST_Simplify(r.geom, 0.0002)) AS geom
      FROM walking_routes r
      JOIN parks p ON p.id = %s
      WHERE ST_Intersects(r.geom, p.geom)
      LIMIT 1000;
    """
    rows = _fetchall(sql, [park_id])
    return JsonResponse({"features": rows})

@require_GET
def routes_within(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        radius_m = float(request.GET.get('radius_m', '1000'))
    except Exception as e:
        return JsonResponse({"error": f"lat,lng required: {e}"}, status=400)

    sql = """
      SELECT id, name, source,
             ST_AsGeoJSON(ST_Simplify(geom, 0.0002)) AS geom
      FROM walking_routes
      WHERE ST_DWithin(
        geography(geom),
        ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,
        %s
      )
      ORDER BY ST_Distance(
        geography(geom),
        ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography
      )
      LIMIT 2000;
    """
    rows = _fetchall(sql, [lng, lat, radius_m, lng, lat])
    return JsonResponse({"features": rows})

@require_GET
def park_containing_point(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except Exception:
        return JsonResponse({"error":"lat,lng required"}, status=400)

    sql = """
      SELECT id, name, category, area_ha,
             ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom,0.0003)) AS geom
      FROM parks
      WHERE ST_Contains(geom, ST_SetSRID(ST_Point(%s,%s),4326))
      LIMIT 1;
    """
    rows = _fetchall(sql, [lng, lat])
    return JsonResponse({"features": rows})

@require_GET
def parks_search(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"features": []})
    sql = """
      SELECT id, name,
             ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.0003)) AS geom
      FROM parks
      WHERE name ILIKE %s
      ORDER BY name
      LIMIT 25;
    """
    rows = _fetchall(sql, [f"%{q}%"])
    return JsonResponse({"features": [{"id": r["id"], "name": r["name"], "geom": r["geom"]} for r in rows]})

@require_GET
def playgrounds_search(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"features": []})
    sql = """
      SELECT id, name,
             ST_AsGeoJSON(geom) AS geom
      FROM playgrounds
      WHERE name ILIKE %s
      ORDER BY name
      LIMIT 25;
    """
    rows = _fetchall(sql, [f"%{q}%"])
    return JsonResponse({"features": [{"id": r["id"], "name": r["name"], "geom": r["geom"]} for r in rows]})

@require_GET
def playground_get(request, pk):
    sql = """
      SELECT id, name, source, ST_AsGeoJSON(geom) AS geom
      FROM playgrounds WHERE id=%s
    """
    rows = _fetchall(sql, [pk])
    if not rows:
        return JsonResponse({"error":"not found"}, status=404)
    return JsonResponse(rows[0])
