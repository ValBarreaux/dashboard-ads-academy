import csv, json
RATE=0.238  # 1 AED = 0.238 EUR (Wise mid-market, 2026-07-24)
rows=[]
with open('ads_meta.tsv') as f:
    r=csv.DictReader(f, delimiter='\t')
    for d in r:
        for k in ['spend','impr','reach','clicks','ctr','cpc','cpm','lclicks','lctr','rdv','vsl','book','etude','v3','thru']:
            d[k]=float(d[k]) if '.' in d[k] else int(d[k])
        rows.append(d)

# Aggregate by ad name (creative)
agg={}
for d in rows:
    a=d['ad']
    x=agg.setdefault(a, {'ad':a,'campaigns':set(),'spend':0,'impr':0,'reach':0,'clicks':0,'lclicks':0,'rdv':0,'vsl':0,'book':0,'etude':0,'v3':0,'thru':0})
    x['campaigns'].add(d['campaign'])
    for k in ['spend','impr','reach','clicks','lclicks','rdv','vsl','book','etude','v3','thru']:
        x[k]+=d[k]

def derive(x):
    sp=x['spend']; im=x['impr']
    x['ctr']=round(x['clicks']/im*100,2) if im else 0
    x['cpm']=round(sp/im*1000,2) if im else 0
    x['cpc']=round(sp/x['clicks'],2) if x['clicks'] else 0
    x['hook']=round(x['v3']/im*100,1) if im else 0          # 3s plays / impressions
    x['cprdv']=round(sp/x['rdv'],2) if x['rdv'] else None    # cost per RDV (AED)
    x['cprdv_eur']=round(x['cprdv']*RATE,2) if x['cprdv'] else None
    x['spend_eur']=round(sp*RATE,2)
    x['cpvsl']=round(sp/x['vsl'],2) if x['vsl'] else None
    return x

ads=[derive(x) for x in agg.values()]
for x in ads: x['campaigns']=', '.join(sorted(x['campaigns']))

# totals
T={'spend':sum(x['spend'] for x in ads),'impr':sum(x['impr'] for x in ads),
   'clicks':sum(x['clicks'] for x in ads),'rdv':sum(x['rdv'] for x in ads),
   'vsl':sum(x['vsl'] for x in ads),'v3':sum(x['v3'] for x in ads)}
T['spend_eur']=T['spend']*RATE
T['cprdv']=T['spend']/T['rdv'] if T['rdv'] else 0
T['ctr']=T['clicks']/T['impr']*100 if T['impr'] else 0

print("=== TOTAUX (lifetime, {} creatives uniques / {} lignes) ===".format(len(ads),len(rows)))
print(f"Depense: {T['spend']:.0f} AED  ({T['spend_eur']:.0f} EUR)")
print(f"Impressions: {T['impr']:,}  |  Clics: {T['clicks']:,}  |  CTR moyen: {T['ctr']:.2f}%")
print(f"RDV (Completed SS App): {T['rdv']}  |  Cout/RDV moyen: {T['cprdv']:.1f} AED ({T['cprdv']*RATE:.1f} EUR)")
print(f"Opt-ins VSL: {T['vsl']}")

# Superwinners: ads with rdv>=3 (statistically meaningful), ranked by cost per RDV
qual=[x for x in ads if x['rdv']>=3]
qual.sort(key=lambda x:x['cprdv'])
print("\n=== SUPERWINNERS -- cout/RDV le plus bas (rdv>=3) ===")
print(f"{'AD':42} {'RDV':>4} {'Dep.AED':>8} {'EUR/RDV':>7} {'CTR':>5} {'Hook':>5}")
for x in qual[:15]:
    print(f"{x['ad'][:42]:42} {x['rdv']:>4} {x['spend']:>8.0f} {x['cprdv_eur']:>7.1f} {x['ctr']:>5.2f} {x['hook']:>5.1f}")

# save clean base
ads_sorted=sorted(ads,key=lambda x:x['spend'],reverse=True)
cols=['ad','campaigns','spend','spend_eur','impr','reach','clicks','ctr','cpc','cpm','rdv','cprdv','cprdv_eur','vsl','cpvsl','book','etude','v3','thru','hook']
with open('ads_base.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader()
    for x in ads_sorted: w.writerow(x)
json.dump({'totals':T,'ads':ads_sorted},open('ads_analysis.json','w'),ensure_ascii=False)
print("\nOK -> ads_base.csv, ads_analysis.json")
