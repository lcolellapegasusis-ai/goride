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
if len(out) < 300:
    raise SystemExit(f'Troppi pochi passi ({len(out)})')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'p': out}, open('data/passes.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('passi totali:', len(out))
