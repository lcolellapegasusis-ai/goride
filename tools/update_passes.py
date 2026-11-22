#!/usr/bin/env python3
"""Passi e valichi su strada da estratti OpenStreetMap ufficiali Geofabrik (niente Overpass).
Uso: update_passes.py IT:italy.pbf CH:switzerland.pbf ... (file già filtrati con osmium)"""
import json, sys, os, datetime
import osmium

ROADS = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
         'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link'}

def ele(t):
    try:
        return int(round(float((t or '').replace(',', '.').split()[0])))
    except Exception:
        return 0

found = {}
for arg in sys.argv[1:]:
    cc, path = arg.split(':', 1)
    passes, onroad = {}, set()
    for o in osmium.FileProcessor(path):
        if o.is_node():
            t = o.tags
            if t.get('mountain_pass') == 'yes' and t.get('name') and o.location.valid():
                passes[o.id] = [round(o.location.lat, 5), round(o.location.lon, 5), t.get('name:it') or t.get('name'), ele(t.get('ele')), cc]
        elif o.is_way():
            if o.tags.get('highway') in ROADS:
                for n in o.nodes:
                    if n.ref in passes:
                        onroad.add(n.ref)
    n = 0
    for i, p in passes.items():
        if i in onroad and i not in found:
            found[i] = p; n += 1
    print(cc or 'alpi', 'passi su strada:', n)
out = list(found.values())
# regione italiana (per l'elenco "per regione"), confini ISTAT da openpolis
try:
    import urllib.request
    from shapely.geometry import shape, Point
    from shapely.prepared import prep
    REG = {'01': 'IT-21', '02': 'IT-23', '03': 'IT-25', '04': 'IT-32', '05': 'IT-34', '06': 'IT-36', '07': 'IT-42', '08': 'IT-45', '09': 'IT-52', '10': 'IT-55',
           '11': 'IT-57', '12': 'IT-62', '13': 'IT-65', '14': 'IT-67', '15': 'IT-72', '16': 'IT-75', '17': 'IT-77', '18': 'IT-78', '19': 'IT-82', '20': 'IT-88'}
    gj = json.loads(urllib.request.urlopen('https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson', timeout=120).read())
    polys = []
    for f in gj['features']:
        code = str(f['properties'].get('reg_istat_code') or f['properties'].get('reg_istat_code_num') or '').zfill(2)
        if code in REG:
            g = shape(f['geometry']); polys.append((REG[code], prep(g), g.bounds))
    n = 0
    for p in out:
        if p[4] not in ('IT', 'SM', ''):
            continue
        pt = Point(p[1], p[0])
        for code, pg, b in polys:
            if b[0] <= p[1] <= b[2] and b[1] <= p[0] <= b[3] and pg.contains(pt):
                p.append(code); n += 1
                if not p[4]: p[4] = 'IT'
                break
    print('passi con regione:', n)
except Exception as e:
    print('regioni non assegnate:', e)
if len(out) < 300:
    raise SystemExit(f'Troppi pochi passi ({len(out)})')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'p': out}, open('data/passes.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('passi totali:', len(out))
