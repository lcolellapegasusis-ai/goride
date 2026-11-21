#!/usr/bin/env python3
"""Concessionarie Harley-Davidson in Europa (OpenStreetMap) -> data/hd.json"""
import json, sys, urllib.request, urllib.parse, datetime, os, time
OVP = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter',
       'https://overpass.kumi.systems/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
BB = '34,-11,71.5,41'

def run(q):
    for k in range(3):
        for u in OVP:
            try:
                req = urllib.request.Request(u, data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'GoRide HD updater'})
                return json.loads(urllib.request.urlopen(req, timeout=200).read())
            except Exception as e:  # noqa
                print('overpass fallito', u, str(e)[:80], file=sys.stderr); time.sleep(10)
    return None

q = (f'[out:json][timeout:180];('
     f'nwr({BB})["shop"~"^motorcycle"]["brand"~"harley",i];'
     f'nwr({BB})["shop"~"^motorcycle"]["name"~"harley",i];'
     f'nwr({BB})["brand"~"^harley",i]["shop"];'
     f');out tags center;')
j = run(q)
if not j:
    raise SystemExit('Overpass non disponibile')
itq = '[out:json][timeout:180];area["ISO3166-1"="IT"]["admin_level"="2"]->.a;(nwr(area.a)["shop"]["brand"~"harley",i];nwr(area.a)["shop"]["name"~"harley",i];);out ids;'
jit = run(itq) or {'elements': []}
ids_it = {(e['type'], e['id']) for e in jit.get('elements', [])}
out = []
for e in j.get('elements', []):
    t = e.get('tags', {})
    la = e.get('lat') or e.get('center', {}).get('lat'); lo = e.get('lon') or e.get('center', {}).get('lon')
    if la is None:
        continue
    cc = (t.get('addr:country') or '').upper()[:2]
    if (e['type'], e['id']) in ids_it:
        cc = 'IT'
    name = t.get('name') or 'Harley-Davidson'
    out.append([round(la, 5), round(lo, 5), name[:60], (t.get('addr:city') or '')[:40], cc,
                (t.get('phone') or t.get('contact:phone') or '').split(';')[0], (t.get('website') or t.get('contact:website') or '')[:120]])
if len(out) < 50:
    raise SystemExit(f'Troppo poche concessionarie ({len(out)})')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'd': out}, open('data/hd.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('concessionarie:', len(out), 'Italia:', sum(1 for x in out if x[4] == 'IT'))
