#!/usr/bin/env python3
"""Elenco dei passi e valichi su strada (OpenStreetMap) per GoRide & Weather -> data/passes.json"""
import json, sys, urllib.request, urllib.parse, datetime, os, time
OVP = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
       'https://maps.mail.ru/osm/tools/overpass/api/interpreter', 'https://overpass.private.coffee/api/interpreter']
ROAD = '["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)$"]'
CC = ['IT', 'SM', 'CH', 'AT', 'FR', 'SI', 'DE', 'ES', 'LI']

def run(q):
    for u in OVP:
        try:
            req = urllib.request.Request(u, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'GoRide passes updater'})
            return json.loads(urllib.request.urlopen(req, timeout=400).read())
        except Exception as e:  # noqa
            print('overpass fallito', u, e, file=sys.stderr); time.sleep(5)
    return None

def ele(t):
    try:
        return int(round(float(t.get('ele', '').replace(',', '.').split()[0])))
    except Exception:
        return 0

out, seen = [], set()
for cc in CC:
    q = (f'[out:json][timeout:360];area["ISO3166-1"="{cc}"]["admin_level"="2"]->.a;'
         f'node(area.a)["mountain_pass"="yes"]->.p;way(bn.p){ROAD}->.w;node.p(w.w)["name"];out body;')
    j = run(q)
    if not j:
        print('salto', cc, file=sys.stderr); continue
    n = 0
    for e in j.get('elements', []):
        if e['id'] in seen:
            continue
        seen.add(e['id']); t = e.get('tags', {})
        out.append([round(e['lat'], 5), round(e['lon'], 5), t.get('name:it') if cc == 'IT' and t.get('name:it') else t['name'], ele(t), cc]); n += 1
    print(cc, n)
if len(out) < 300:
    raise SystemExit(f'Troppi pochi passi ({len(out)})')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'p': out}, open('data/passes.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('passi totali:', len(out))
