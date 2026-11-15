#!/usr/bin/env python3
"""Scarica l'anagrafica ufficiale dei distributori italiani (MIMIT, open data IODL 2.0)
e i prezzi delle ore 8, e produce data/fuel_it.json compatto per GoRide & Weather."""
import json, sys, urllib.request, datetime, os

BASES = ['https://www.mimit.gov.it/images/exportCSV/', 'https://www.mise.gov.it/images/exportCSV/']

def get(name):
    last = None
    for b in BASES:
        try:
            req = urllib.request.Request(b + name, headers={'User-Agent': 'Mozilla/5.0 (GoRide fuel updater)'})
            data = urllib.request.urlopen(req, timeout=180).read()
            for enc in ('utf-8', 'latin-1'):
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    pass
        except Exception as e:  # noqa
            last = e
            print('download fallito', b + name, e, file=sys.stderr)
    raise SystemExit(f'Impossibile scaricare {name}: {last}')

def split_rows(text, key):
    lines = text.splitlines()
    hi = next(i for i, l in enumerate(lines[:10]) if key.lower() in l.lower())
    head = lines[hi]
    sep = '|' if head.count('|') > head.count(';') else ';'
    for l in lines[hi + 1:]:
        if l.strip():
            yield [p.strip() for p in l.split(sep)]

def num(x):
    try:
        return float(x.replace(',', '.'))
    except Exception:
        return None

ana = get('anagrafica_impianti_attivi.csv')
pre = get('prezzo_alle_8.csv')

prices = {}
for p in split_rows(pre, 'idImpianto'):
    if len(p) < 4:
        continue
    pid, desc, pr, self_ = p[0], p[1].lower(), num(p[2]), p[3]
    if not pr or pr < 0.3 or pr > 5:
        continue
    k = 'b' if 'benzina' in desc else 'd' if ('gasolio' in desc or 'diesel' in desc) else 'g' if 'gpl' in desc else 'm' if ('metano' in desc or 'gnc' in desc or 'gnl' in desc) else None
    if not k:
        continue
    d = prices.setdefault(pid, {})
    # preferisco il prezzo self, altrimenti il minimo servito
    cur = d.get(k)
    is_self = self_.strip() in ('1', 'true', 'True')
    if cur is None or (is_self and not cur[1]) or (is_self == cur[1] and pr < cur[0]):
        d[k] = (pr, is_self)

brands, bidx, out = [], {}, []
for r in split_rows(ana, 'idImpianto'):
    if len(r) < 10:
        continue
    pid, gest, band, tipo, nome = r[0], r[1], r[2], r[3], r[4]
    lat, lon = num(r[-2]), num(r[-1])
    comune = r[-4] if len(r) >= 10 else ''
    if lat is None or lon is None or not (35 < lat < 48.2 and 6 < lon < 19.5):
        continue
    if band not in bidx:
        bidx[band] = len(brands); brands.append(band)
    pz = prices.get(pid, {})
    def pv(k):
        return int(round(pz[k][0] * 1000)) if k in pz else 0
    out.append([round(lat, 5), round(lon, 5), bidx[band], (nome or gest)[:40], 1 if 'autostrad' in tipo.lower() else 0,
                pv('b'), pv('d'), pv('g'), pv('m'), comune.title()[:30]])

if len(out) < 5000:
    raise SystemExit(f'Troppi pochi impianti ({len(out)}): non aggiorno il file')
os.makedirs('data', exist_ok=True)
json.dump({'v': datetime.date.today().isoformat(), 'b': brands, 's': out}, open('data/fuel_it.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('impianti:', len(out), 'marchi:', len(brands))
