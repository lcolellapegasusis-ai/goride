#!/usr/bin/env python3
"""Elenco dei passi e valichi su strada (OpenStreetMap) per GoRide & Weather -> data/passes.json
Interroga piccoli riquadri 2x2 gradi (veloci) invece di interi Paesi."""
import json, sys, urllib.request, urllib.parse, datetime, os, time
OVP = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter',
       'https://overpass.kumi.systems/api/interpreter']
ROAD = '["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)$"]'
LAT = (36, 52); LON = (-10, 20)   # Italia, Alpi, Francia, Spagna, Germania meridionale, Slovenia, Croazia
CC = ['IT', 'SM', 'CH', 'AT', 'FR', 'SI', 'DE', 'ES', 'LI']
T0 = time.time()

def run(q, to):
    for u in OVP:
        try:
            req = urllib.request.Request(u, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'GoRide passes updater'})
            return json.loads(urllib.request.urlopen(req, timeout=to).read())
        except Exception as e:  # noqa
            print('overpass fallito', u, str(e)[:80], file=sys.stderr); time.sleep(2)
    return None

def ele(t):
    try:
        return int(round(float(t.get('ele', '').replace(',', '.').split()[0])))
    except Exception:
        return 0

found = {}
for la in range(LAT[0], LAT[1], 2):
    for lo in range(LON[0], LON[1], 2):
        if time.time() - T0 > 2400:
            break
        bb = f'{la},{lo},{la+2},{lo+2}'
        q = f'[out:json][timeout:80];node({bb})["mountain_pass"="yes"]["name"]->.p;way(bn.p){ROAD}->.w;node.p(w.w);out body;'
        j = run(q, 100)
        if j is None:
            print('riquadro saltato', bb, file=sys.stderr); continue
        for e in j.get('elements', []):
            t = e.get('tags', {})
            found[e['id']] = [round(e['lat'], 5), round(e['lon'], 5), t.get('name:it') or t['name'], ele(t), '']
        print(bb, len(j.get('elements', [])))
# Paese di appartenenza (serve solo per l'elenco "per Paese"); se fallisce resta vuoto
for cc in CC:
    j = run(f'[out:json][timeout:120];area["ISO3166-1"="{cc}"]["admin_level"="2"]->.a;node(area.a)["mountain_pass"="yes"]["name"];out ids;', 150)
    if j:
        for e in j.get('elements', []):
            if e['id'] in found and not found[e['id']][4]:
                found[e['id']][4] = cc
out = list(found.values())
if len(out) < 300:
    raise SystemExit(f'Troppi pochi passi ({len(out)})')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'p': out}, open('data/passes.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('passi totali:', len(out), 'tempo', int(time.time() - T0), 's')
