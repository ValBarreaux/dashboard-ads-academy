import json, csv, html, datetime
from collections import Counter
RATE=0.238
_MOIS=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
_today=datetime.date.today()
today=f"{_today.day} {_MOIS[_today.month-1]} {_today.year}"
d=json.load(open('ads_analysis.json')); T=d['totals']; ads=d['ads']
def eur(a): return a*RATE
def num(n): return f"{n:,.0f}".replace(","," ")
acct_cprdv_aed=T['cprdv']; acct_cprdv_eur=eur(acct_cprdv_aed)
acct_cpm_aed=T['spend']/T['impr']*1000 if T['impr'] else 0
life={a['ad']:a for a in ads}

for a in ads:
    a['cpl_eur']= eur(a['spend'])/a['vsl'] if a['vsl'] else None
    a['vcr']= a['rdv']/a['vsl']*100 if a['vsl'] else None

tot_clicks=sum(a['clicks'] for a in ads)
tot_lead=int(T['vsl']); tot_rdv=int(T['rdv']); spend_e=eur(T['spend'])
acc={
 'ctr':T['ctr'],
 'cpc':spend_e/tot_clicks if tot_clicks else 0,
 'cpl':spend_e/tot_lead if tot_lead else None,
 'lpc':tot_lead/tot_clicks*100 if tot_clicks else 0,
 'vcr':tot_rdv/tot_lead*100 if tot_lead else None,
 'cps':spend_e/tot_rdv if tot_rdv else None,
}
DIRS={'up':'<span class="dir up">↑ plus haut = mieux</span>','down':'<span class="dir down">↓ plus bas = mieux</span>'}
PILL={'ok':'<span class="bpill ok">✅ tu bats la cible</span>','warn':'<span class="bpill warn">⚠️ marge de progrès</span>','na':'<span class="bpill na">à venir (CRM)</span>'}
stages=[
 ("① Ads", [("CTR (lien)","0,5–1 %",f"{acc['ctr']:.2f} %","ok","up"),("CPC","1–3 €",f"{acc['cpc']:.2f} €","ok","down"),("CPM","≈10 €",f"{eur(acct_cpm_aed):.1f} €","ok","down")]),
 ("② Lead (opt-in)", [("CPL","5–15 €",(f"{acc['cpl']:.2f} €" if acc['cpl'] else "—"),"ok","down"),("Taux d'opt-in (LPC)","≈20 %",f"{acc['lpc']:.1f} %","warn","up")]),
 ("③ VSL → RDV", [("VCR (opt-in→RDV)","≈15–20 %",(f"{acc['vcr']:.1f} %" if acc['vcr'] else "—"),"warn","up"),("Coût/RDV (CPS)","50–150 €",(f"{acc['cps']:.0f} €" if acc['cps'] else "—"),"ok","down")]),
 ("④ Call (show-up)", [("SUR (présence au call)","≈70 %","—","na","up"),("Coût/call (CSS)","60–360 €","—","na","down")]),
 ("⑤ Client", [("CCR (call→vente)","≈15 %","—","na","up"),("CPA (coût client)","300–1800 €","—","na","down")]),
]
fcards=""
for st,mets in stages:
    rows=""
    for name,tgt,act,kind,sens in mets:
        cls={'ok':'st-ok','warn':'st-warn','na':'st-na'}[kind]
        rows+=f'<div class="metric"><div class="mrow"><span class="mn">{name}</span> {DIRS[sens]}</div><div>cible <span class="tgt">{tgt}</span> · toi <span class="act {cls}">{act}</span> {PILL[kind]}</div></div>'
    fcards+=f'<div class="fstage"><div class="st">{st}</div>{rows}</div>'
benchpanel=f"""<div class="bench">
<div class="benchlead"><b>Comment lire (pour l'équipe) :</b> <span class="dir up">↑ plus haut = mieux</span> <span class="dir down">↓ plus bas = mieux</span> · {PILL['ok']} · {PILL['warn']}. Étalon = funnel VSL des <b>frères Teliosa</b> (500K€/mois) ; « toi » = tes chiffres réels (lifetime).</div>
<div class="funnel">{fcards}</div>
<div class="note">Lecture rapide : tu <b>bats la cible sur tout le haut de funnel</b> (CTR au-dessus = bien ; CPC, CPL ~3 € et coût/RDV ~27 € en-dessous = très bien). Tes 2 leviers de progression (⚠️) = le <b>taux d'opt-in</b> et le <b>VCR</b> — il faut les faire <b>monter</b>.</div>
</div>"""

act=[]
with open('active_7d.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        for k in ['spend','impr','clicks','ctr','cpc','lead','rdv','lpv','v3']: r[k]=float(r[k])
        r['v3hookpct']= r['v3']/r['impr']*100 if r['impr'] else 0
        act.append(r)
TARGET=114.0
def reco(r):
    sp=r['spend']; rdv=int(r['rdv']); ctr=r['ctr']; hook=r['v3hookpct']
    cprdv=sp/rdv if rdv else None; cprdv_e=eur(cprdv) if cprdv else None
    L=life.get(r['ad']); lifenote=""
    if L and L['rdv']>=10: lifenote=f"Gagnante confirmée (lifetime : {L['rdv']} RDV à {L['cprdv_eur']:.0f} €/RDV)."
    crea=""
    if ctr>=4: crea="Accroche exceptionnelle (CTR élevé)."
    elif hook>=90: crea="Hook fort."
    if rdv>=2 and cprdv<=95:
        tag,cls="SCALER","scale"; a=f"Augmenter le budget (+20–30 %). {cprdv_e:.0f} €/RDV, sous ta moyenne."
        if sp<350: a+=" Et décliner des variantes proches pour capter plus de reach."
    elif rdv>=1 and cprdv<=95 and sp<200:
        tag,cls="PÉPITE À SCALER","gem"; a=f"Winner sous-exploité ({cprdv_e:.0f} €/RDV sur {sp:.0f} AED seulement). Monter le budget + dupliquer."
    elif rdv>=1 and cprdv>170:
        tag,cls="À SURVEILLER / BAISSER","watch"; a=f"Coût/RDV élevé cette semaine ({cprdv_e:.0f} €/RDV vs {acct_cprdv_eur:.0f} € moyen). Baisser ou couper si ça persiste."
    elif rdv>=1:
        tag,cls="MAINTENIR","keep"; a=f"Proche de ta moyenne ({cprdv_e:.0f} €/RDV). Garder et surveiller."
    else:
        if sp>=2*TARGET: tag,cls="ALERTE — 0 RDV","alert"; a=f"{sp:.0f} AED sans aucun RDV (seuil ~{2*TARGET:.0f} AED dépassé). Surveiller de près, couper si toujours 0 RDV d'ici ~100 AED."
        elif sp>=25: tag,cls="APPRENTISSAGE","learn"; a=f"En apprentissage ({sp:.0f} AED, 0 RDV). Laisser tourner, décision à ~{2*TARGET:.0f} AED."
        else: tag,cls="VIENT DE LANCER","new"; a=f"Trop tôt pour juger ({sp:.0f} AED). Laisser accumuler de la donnée."
    return dict(tag=tag,cls=cls,act=a,crea=crea,life=lifenote,cprdv=cprdv,cprdv_e=cprdv_e)
for r in act: r['R']=reco(r)
order={"SCALER":0,"PÉPITE À SCALER":1,"MAINTENIR":2,"À SURVEILLER / BAISSER":3,"ALERTE — 0 RDV":4,"APPRENTISSAGE":5,"VIENT DE LANCER":6}
act.sort(key=lambda r:(order[r['R']['tag']], -r['spend']))
s7=sum(r['spend'] for r in act); rdv7=sum(int(r['rdv']) for r in act); cprdv7=s7/rdv7 if rdv7 else 0
lead7=sum(int(r['lead']) for r in act); cpl7=s7/lead7 if lead7 else 0; lpv7=sum(int(r['lpv']) for r in act)
c=Counter(r['R']['tag'] for r in act)
def chip(t,label,cls): return f'<span class="chip {cls}">{c.get(t,0)} {label}</span>' if c.get(t,0) else ''
chips=chip("SCALER","à scaler","scale")+chip("PÉPITE À SCALER","pépite(s)","gem")+chip("MAINTENIR","à maintenir","keep")+chip("À SURVEILLER / BAISSER","à surveiller","watch")+chip("ALERTE — 0 RDV","alerte(s)","alert")+chip("APPRENTISSAGE","en apprentissage","learn")+chip("VIENT DE LANCER","viennent de lancer","new")

pilot_rows=[]
for r in act:
    R=r['R']; rdv=int(r['rdv']); lead=int(r['lead'])
    cprdv_disp=f"{R['cprdv_e']:.0f} € <span class='aed'>({R['cprdv']:.0f} AED)</span>" if R['cprdv'] else "<span class='none'>—</span>"
    cpl_disp=f"{eur(r['spend']/lead):.0f} € <span class='aed'>({r['spend']/lead:.0f} AED)</span>" if lead else "<span class='none'>—</span>"
    notes=" ".join(x for x in [R['crea'],R['life']] if x)
    isely='ely' in r['ad'].lower()
    pilot_rows.append(f"""<tr class="pr {R['cls']}">
<td class="adname">{'🎯 ' if isely else ''}{html.escape(r['ad'])}</td>
<td class="r">{eur(r['spend']):.0f} €<span class="aed">{r['spend']:.0f} AED</span></td>
<td class="r">{num(r['impr'])}</td><td class="r">{r['ctr']:.2f}%</td><td class="r hook">{r['v3hookpct']:.0f}%</td>
<td class="r">{num(r['lpv'])}</td><td class="r strong">{lead}</td><td class="r cprdv">{cpl_disp}</td>
<td class="r strong">{rdv}</td><td class="r cprdv">{cprdv_disp}</td>
<td><span class="tag {R['cls']}">{R['tag']}</span><div class="reco">{html.escape(R['act'])}{(' <b>'+html.escape(notes)+'</b>') if notes else ''}</div></td></tr>""")

def cpl_cls(v):
    if v is None: return 'none'
    return 'good' if v<=8 else ('mid' if v<=15 else 'bad')
def vcr_cls(v):
    if v is None: return 'none'
    return 'good' if v>=15 else ('mid' if v>=8 else 'bad')
hist_rows=[]
for a in ads:
    cprdv_e=a['cprdv_eur']
    if a['rdv']==0: cls='none'; disp='—'
    else:
        cls='good' if cprdv_e<=20 else ('mid' if cprdv_e<=35 else 'bad'); disp=f"{cprdv_e:.1f} € <span class='aed'>({num(a['cprdv'])} AED)</span>"
    win='★' if (a['rdv']>=3 and cprdv_e is not None and cprdv_e<=acct_cprdv_eur) else ''
    cpl_disp=f"{a['cpl_eur']:.1f} €" if a['cpl_eur'] is not None else "—"
    vcr_disp=f"{a['vcr']:.1f}%" if a['vcr'] is not None else "—"
    hist_rows.append(f"""<tr data-spend="{a['spend']}" data-rdv="{a['rdv']}" data-cprdv="{a['cprdv_eur'] or 999999}" data-ctr="{a['ctr']}" data-hook="{a['hook']}" data-cpl="{a['cpl_eur'] or 999999}" data-vcr="{a['vcr'] or -1}" data-name="{html.escape(a['ad']).lower()}">
<td class="adname">{'<span class=star>★</span> ' if win else ''}{html.escape(a['ad'])}<div class="camp">{html.escape(a['campaigns'])}</div></td>
<td class="r">{a['spend_eur']:.0f} €<span class="aed">{num(a['spend'])} AED</span></td>
<td class="r">{num(a['impr'])}</td><td class="r">{a['ctr']:.2f}%</td><td class="r hook">{a['hook']:.0f}%</td>
<td class="r">{a['vsl']}</td><td class="r {cpl_cls(a['cpl_eur'])}">{cpl_disp}</td>
<td class="r strong">{a['rdv']}</td><td class="r cprdv {cls}">{disp}</td><td class="r {vcr_cls(a['vcr'])}">{vcr_disp}</td></tr>""")

by_rdv=sorted([a for a in ads if a['rdv']>0],key=lambda x:x['rdv'],reverse=True)[:10]; maxr=max((a['rdv'] for a in by_rdv), default=1)
bars=''.join(f"""<div class="barrow"><div class="barlabel">{html.escape(a['ad'])}</div><div class="bartrack"><div class="bar" style="width:{a['rdv']/maxr*100:.1f}%"></div><span class="barval">{a['rdv']} RDV · {a['cprdv_eur']:.0f} €/RDV</span></div></div>""" for a in by_rdv)
winners=sorted([a for a in ads if a['rdv']>=3],key=lambda x:x['cprdv'])[:6]
wcards=''.join(f"""<div class="wcard"><div class="wname">{html.escape(a['ad'])}</div><div class="wbig">{a['cprdv_eur']:.1f} €<span>/RDV</span></div><div class="wsub">{a['rdv']} RDV · {a['spend_eur']:.0f} € · CTR {a['ctr']:.2f}% · Hook {a['hook']:.0f}%</div></div>""" for a in winners)

# ---------- ROAS (ventes attribuees aux pubs) ----------
import os as _os
sales={"avant":{"ca_signe":0,"cash":0,"ventes":0,"by_ad_id":{}},"maintenant":{"ca_signe":0,"cash":0,"ventes":0,"by_ad_id":{}}}
if _os.path.exists('sales_roas.json'):
    try: sales=json.load(open('sales_roas.json'))
    except Exception: pass
spend_eur=eur(T['spend'])
ca_pub=sales['avant']['ca_signe']+sales['maintenant']['ca_signe']
cash_pub=sales['avant']['cash']+sales['maintenant']['cash']
nventes=sales['avant']['ventes']+sales['maintenant']['ventes']
roas_signe=ca_pub/spend_eur if spend_eur else 0
roas_cash=cash_pub/spend_eur if spend_eur else 0
_rcls=lambda v:'good' if v>=2 else ('mid' if v>=1 else 'bad')
byad=sales['maintenant']['by_ad_id']
if byad:
    _rows=''.join(f"<tr><td class='adname'>{aid}</td><td class='r strong'>{v['ventes']}</td><td class='r'>{num(v['ca'])} €</td></tr>" for aid,v in sorted(byad.items(),key=lambda x:-x[1]['ca']))
    roas_ad_html=f"<h3>ROAS par ad — calls pub closés (Hedy)</h3><table><thead><tr><th>Ad (id)</th><th class='r'>Ventes</th><th class='r'>CA</th></tr></thead><tbody>{_rows}</tbody></table>"
else:
    roas_ad_html="<h3>ROAS par ad — « maintenant » (à venir)</h3><p class='ptxt'>Aucun call issu d'une pub n'a encore closé côté Hedy. Le ROAS <b>par ad précise</b> se remplira tout seul dès la première vente pub attribuée (ad_id dans sa sheet).</p>"
roas_section=f"""<h2 class="s1">\U0001f4b0 ROAS — retour sur dépense publicitaire</h2>
<div class="kpis">
<div class="kpi"><div class="lab">Dépense pub totale</div><div class="val">{num(spend_eur)} €</div></div>
<div class="kpi"><div class="lab">CA attribué aux pubs</div><div class="val">{num(ca_pub)} € <small>{nventes} ventes</small></div></div>
<div class="kpi"><div class="lab">Encaissé à ce jour</div><div class="val">{num(cash_pub)} €</div></div>
<div class="kpi"><div class="lab">ROAS signé</div><div class="val {_rcls(roas_signe)}">{roas_signe:.2f}x</div></div>
<div class="kpi"><div class="lab">ROAS encaissé</div><div class="val {_rcls(roas_cash)}">{roas_cash:.2f}x</div></div>
</div>
<div class="note gold"><b>Comment c'est calculé :</b> une vente compte comme « pub » uniquement si la ligne a un <b>ad_id</b> (sheet Hedy) ou la source <b>« Ads »</b> (ta sheet) — l'organique (FB / insta / mails) est exclu. <b>ROAS signé</b> = CA contractualisé ÷ dépense pub ; <b>ROAS encaissé</b> = cash déjà encaissé ÷ dépense (il monte à mesure que les Split-Pay se paient). Dépense = total lifetime.</div>
<div class="panel" style="margin-top:14px">{roas_ad_html}</div>"""

CSS=open('dash_css.txt').read()
H=f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard Ads — Académie Excellence</title><style>{CSS}</style></head><body>
<div class="head"><div><h1>⚽ Dashboard Publicités — Académie Excellence</h1><div class="sub">Compte <b>Valentin Barreaux_Coaching</b> · Monitoring temps réel · Pilotage + Benchmark + ROAS + Historique</div></div>
<div style="text-align:right"><div class="badge">Mis à jour : {today}</div><div class="badge" style="margin-top:6px">1 AED = 0,238 €</div></div></div>

<h2 class="s1" style="margin-top:24px">📐 BENCHMARK — Funnel VSL de référence (frères Teliosa) vs tes chiffres</h2>
{benchpanel}

<div class="section-pilot">
<h2 class="s1">🎯 PILOTAGE — Ads actives (7 derniers jours)</h2>
<div class="sub2">{len(act)} ads ont diffusé · {eur(s7):.0f} € ({num(s7)} AED) · <b>{lead7} prospects</b> ({eur(cpl7):.0f} €/prospect) · {num(lpv7)} vues landing · {rdv7} RDV ({eur(cprdv7):.0f} €/RDV). 🎯 = ads Ely.</div>
<div class="chips">{chips}</div>
<div class="tablewrap"><table class="pilot"><thead><tr><th>Ad active</th><th class="r">Dépense 7j</th><th class="r">Impr.</th><th class="r">CTR</th><th class="r">Hook</th><th class="r">Vues landing</th><th class="r">Prospects</th><th class="r">Coût/prospect</th><th class="r">RDV</th><th class="r">Coût/RDV</th><th>Reco d'action</th></tr></thead><tbody>{''.join(pilot_rows)}</tbody></table></div>
<div class="note gold"><b>💡 Répliquer les superwinners :</b> pour chaque ad « Scaler » ou « Pépite », crée 2–3 variantes proches (même angle/hook) et teste-les — c'est comme ça qu'on va chercher du reach en gardant l'efficacité.</div>
</div>

<h2>📈 KPI globaux (lifetime)</h2>
<div class="kpis">
<div class="kpi"><div class="lab">Dépense totale</div><div class="val">{eur(T['spend']):,.0f} € <small>/ {num(T['spend'])} AED</small></div></div>
<div class="kpi"><div class="lab">RDV générés</div><div class="val">{T['rdv']:.0f}</div></div>
<div class="kpi"><div class="lab">Leads (opt-in VSL)</div><div class="val">{tot_lead}</div></div>
<div class="kpi"><div class="lab">CPL moyen</div><div class="val">{(f"{acc['cpl']:.2f} €" if acc['cpl'] else "—")} <small>cible 5–15 €</small></div></div>
<div class="kpi"><div class="lab">VCR moyen</div><div class="val">{(f"{acc['vcr']:.1f}%" if acc['vcr'] else "—")} <small>cible ~15–20%</small></div></div>
<div class="kpi"><div class="lab">Coût/RDV moyen</div><div class="val">{acct_cprdv_eur:.1f} € <small>/ {acct_cprdv_aed:.0f} AED</small></div></div>
</div>

<h2>🏆 Superwinners historiques — meilleur coût/RDV (≥ 3 RDV)</h2>
<div class="wcards">{wcards}</div>

<div class="grid2" style="margin-top:24px">
<div class="panel"><h3>Top 10 créatives par volume de RDV (lifetime)</h3>{bars}</div>
<div class="panel"><h3>Couche ventes / ROAS</h3><p class="ptxt">La couche ventes est branchée sur <b>ta tracking sheet</b> (historique « Ads ») + celle de <b>Hedy</b> (en cours, par ad_id). Voir la section <b>ROAS</b> juste en dessous.</p></div>
</div>

{roas_section}

<h2>📊 Historique complet — toutes les créatives ({len(ads)})</h2>
<div class="tabhead"><div class="legend">Trier : clic sur l'en-tête · <b>CPL</b> cible 5–15 € (<span class="good">vert</span>≤8 · <span class="mid">jaune</span>≤15 · <span class="bad">rouge</span>&gt;15) · <b>VCR</b> cible ~15% (<span class="good">vert</span>≥15% · <span class="mid">jaune</span>≥8%)</div><input class="search" id="s" placeholder="Rechercher une ad…" oninput="filt()"></div>
<div class="tablewrap"><table id="t"><thead><tr>
<th onclick="srt('name')">Créative / Campagne</th><th onclick="srt('spend')" class="r">Dépense</th><th onclick="srt('impr')" class="r">Impr.</th><th onclick="srt('ctr')" class="r">CTR</th><th onclick="srt('hook')" class="r">Hook</th><th class="r">Leads</th><th onclick="srt('cpl')" class="r">CPL</th><th onclick="srt('rdv')" class="r">RDV</th><th onclick="srt('cprdv')" class="r">Coût/RDV</th><th onclick="srt('vcr')" class="r">VCR</th></tr></thead><tbody id="tb">{''.join(hist_rows)}</tbody></table></div>

<div class="foot">Extraction automatique via l'API Meta Ads + ventes via les tracking sheets (compte de service Google). Lead = event « Prospect ». RDV = « Completed SS Application ». ROAS = ventes marquées « Ads »/ad_id ÷ dépense pub. Benchmark = funnel VSL frères Teliosa. Taux AED→EUR du {today}.</div>
<script>
const tb=document.getElementById('tb');let dir={{}};
function srt(k){{const rows=[...tb.querySelectorAll('tr')];if(dir[k]===undefined){{dir[k]=(k==='name');}}else{{dir[k]=!dir[k];}}const asc=dir[k];
rows.sort((a,b)=>{{let x,y;if(k=='name'){{x=a.dataset.name;y=b.dataset.name;return asc?x.localeCompare(y):y.localeCompare(x);}}x=+a.dataset[k];y=+b.dataset[k];return asc?x-y:y-x;}});rows.forEach(r=>tb.appendChild(r));}}
function filt(){{const q=document.getElementById('s').value.toLowerCase();tb.querySelectorAll('tr').forEach(r=>{{r.style.display=r.dataset.name.includes(q)?'':'none';}});}}
srt('rdv');
</script></body></html>"""
open('dashboard_ads.html','w').write(H)
print("written",len(H),"bytes · ROAS signe",round(roas_signe,2),"x · CA pub",round(ca_pub),"EUR")
import json, csv, html, datetime
from collections import Counter
RATE=0.238
_MOIS=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
_today=datetime.date.today()
today=f"{_today.day} {_MOIS[_today.month-1]} {_today.year}"
d=json.load(open('ads_analysis.json')); T=d['totals']; ads=d['ads']
def eur(a): return a*RATE
def num(n): return f"{n:,.0f}".replace(","," ")
acct_cprdv_aed=T['cprdv']; acct_cprdv_eur=eur(acct_cprdv_aed)
acct_cpm_aed=T['spend']/T['impr']*1000 if T['impr'] else 0
life={a['ad']:a for a in ads}

# per-creative CPL (spend/vsl) & VCR (rdv/vsl)
for a in ads:
    a['cpl_eur']= eur(a['spend'])/a['vsl'] if a['vsl'] else None
    a['vcr']= a['rdv']/a['vsl']*100 if a['vsl'] else None

# ---------- account funnel vs Teliosa benchmark ----------
tot_clicks=sum(a['clicks'] for a in ads)
tot_lead=int(T['vsl']); tot_rdv=int(T['rdv']); spend_e=eur(T['spend'])
acc={
 'ctr':T['ctr'],
 'cpc':spend_e/tot_clicks if tot_clicks else 0,
 'cpl':spend_e/tot_lead if tot_lead else None,
 'lpc':tot_lead/tot_clicks*100 if tot_clicks else 0,
 'vcr':tot_rdv/tot_lead*100 if tot_lead else None,
 'cps':spend_e/tot_rdv if tot_rdv else None,
}
DIRS={'up':'<span class="dir up">↑ plus haut = mieux</span>','down':'<span class="dir down">↓ plus bas = mieux</span>'}
PILL={'ok':'<span class="bpill ok">✅ tu bats la cible</span>','warn':'<span class="bpill warn">⚠️ marge de progrès</span>','na':'<span class="bpill na">à venir (CRM)</span>'}
# (name, cible, ta_valeur, statut, sens)  sens: up = plus haut mieux · down = plus bas mieux
stages=[
 ("① Ads", [("CTR (lien)","0,5–1 %",f"{acc['ctr']:.2f} %","ok","up"),("CPC","1–3 €",f"{acc['cpc']:.2f} €","ok","down"),("CPM","≈10 €",f"{eur(acct_cpm_aed):.1f} €","ok","down")]),
 ("② Lead (opt-in)", [("CPL","5–15 €",(f"{acc['cpl']:.2f} €" if acc['cpl'] else "—"),"ok","down"),("Taux d'opt-in (LPC)","≈20 %",f"{acc['lpc']:.1f} %","warn","up")]),
 ("③ VSL → RDV", [("VCR (opt-in→RDV)","≈15–20 %",(f"{acc['vcr']:.1f} %" if acc['vcr'] else "—"),"warn","up"),("Coût/RDV (CPS)","50–150 €",(f"{acc['cps']:.0f} €" if acc['cps'] else "—"),"ok","down")]),
 ("④ Call (show-up)", [("SUR (présence au call)","≈70 %","—","na","up"),("Coût/call (CSS)","60–360 €","—","na","down")]),
 ("⑤ Client", [("CCR (call→vente)","≈15 %","—","na","up"),("CPA (coût client)","300–1800 €","—","na","down")]),
]
fcards=""
for st,mets in stages:
    rows=""
    for name,tgt,act,kind,sens in mets:
        cls={'ok':'st-ok','warn':'st-warn','na':'st-na'}[kind]
        rows+=f'<div class="metric"><div class="mrow"><span class="mn">{name}</span> {DIRS[sens]}</div><div>cible <span class="tgt">{tgt}</span> · toi <span class="act {cls}">{act}</span> {PILL[kind]}</div></div>'
    fcards+=f'<div class="fstage"><div class="st">{st}</div>{rows}</div>'
benchpanel=f"""<div class="bench">
<div class="benchlead"><b>Comment lire (pour l'équipe) :</b> <span class="dir up">↑ plus haut = mieux</span> <span class="dir down">↓ plus bas = mieux</span> · {PILL['ok']} · {PILL['warn']}. Étalon = funnel VSL des <b>frères Teliosa</b> (500K€/mois) ; « toi » = tes chiffres réels (lifetime).</div>
<div class="funnel">{fcards}</div>
<div class="note">Lecture rapide : tu <b>bats la cible sur tout le haut de funnel</b> (CTR au-dessus = bien ; CPC, CPL ~3 € et coût/RDV ~27 € en-dessous = très bien). Tes 2 leviers de progression (⚠️) = le <b>taux d'opt-in</b> et le <b>VCR</b> — il faut les faire <b>monter</b>. Les étapes Call/Client s'activeront avec le CRM.</div>
</div>"""

# ---------- active 7d + reco ----------
act=[]
with open('active_7d.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        for k in ['spend','impr','clicks','ctr','cpc','lead','rdv','lpv','v3']: r[k]=float(r[k])
        r['v3hookpct']= r['v3']/r['impr']*100 if r['impr'] else 0
        act.append(r)
TARGET=114.0
def reco(r):
    sp=r['spend']; rdv=int(r['rdv']); ctr=r['ctr']; hook=r['v3hookpct']
    cprdv=sp/rdv if rdv else None; cprdv_e=eur(cprdv) if cprdv else None
    L=life.get(r['ad']); lifenote=""
    if L and L['rdv']>=10: lifenote=f"Gagnante confirmée (lifetime : {L['rdv']} RDV à {L['cprdv_eur']:.0f} €/RDV)."
    crea=""
    if ctr>=4: crea="Accroche exceptionnelle (CTR élevé)."
    elif hook>=90: crea="Hook fort."
    if rdv>=2 and cprdv<=95:
        tag,cls="SCALER","scale"; a=f"Augmenter le budget (+20–30 %). {cprdv_e:.0f} €/RDV, sous ta moyenne."
        if sp<350: a+=" Et décliner des variantes proches pour capter plus de reach."
    elif rdv>=1 and cprdv<=95 and sp<200:
        tag,cls="PÉPITE À SCALER","gem"; a=f"Winner sous-exploité ({cprdv_e:.0f} €/RDV sur {sp:.0f} AED seulement). Monter le budget + dupliquer."
    elif rdv>=1 and cprdv>170:
        tag,cls="À SURVEILLER / BAISSER","watch"; a=f"Coût/RDV élevé cette semaine ({cprdv_e:.0f} €/RDV vs {acct_cprdv_eur:.0f} € moyen). Baisser ou couper si ça persiste."
    elif rdv>=1:
        tag,cls="MAINTENIR","keep"; a=f"Proche de ta moyenne ({cprdv_e:.0f} €/RDV). Garder et surveiller."
    else:
        if sp>=2*TARGET: tag,cls="ALERTE — 0 RDV","alert"; a=f"{sp:.0f} AED sans aucun RDV (seuil ~{2*TARGET:.0f} AED dépassé). Surveiller de près, couper si toujours 0 RDV d'ici ~100 AED."
        elif sp>=25: tag,cls="APPRENTISSAGE","learn"; a=f"En apprentissage ({sp:.0f} AED, 0 RDV). Laisser tourner, décision à ~{2*TARGET:.0f} AED."
        else: tag,cls="VIENT DE LANCER","new"; a=f"Trop tôt pour juger ({sp:.0f} AED). Laisser accumuler de la donnée."
    return dict(tag=tag,cls=cls,act=a,crea=crea,life=lifenote,cprdv=cprdv,cprdv_e=cprdv_e)
for r in act: r['R']=reco(r)
order={"SCALER":0,"PÉPITE À SCALER":1,"MAINTENIR":2,"À SURVEILLER / BAISSER":3,"ALERTE — 0 RDV":4,"APPRENTISSAGE":5,"VIENT DE LANCER":6}
act.sort(key=lambda r:(order[r['R']['tag']], -r['spend']))
s7=sum(r['spend'] for r in act); rdv7=sum(int(r['rdv']) for r in act); cprdv7=s7/rdv7 if rdv7 else 0
lead7=sum(int(r['lead']) for r in act); cpl7=s7/lead7 if lead7 else 0; lpv7=sum(int(r['lpv']) for r in act)
c=Counter(r['R']['tag'] for r in act)
def chip(t,label,cls): return f'<span class="chip {cls}">{c.get(t,0)} {label}</span>' if c.get(t,0) else ''
chips=chip("SCALER","à scaler","scale")+chip("PÉPITE À SCALER","pépite(s)","gem")+chip("MAINTENIR","à maintenir","keep")+chip("À SURVEILLER / BAISSER","à surveiller","watch")+chip("ALERTE — 0 RDV","alerte(s)","alert")+chip("APPRENTISSAGE","en apprentissage","learn")+chip("VIENT DE LANCER","viennent de lancer","new")

pilot_rows=[]
for r in act:
    R=r['R']; rdv=int(r['rdv']); lead=int(r['lead'])
    cprdv_disp=f"{R['cprdv_e']:.0f} € <span class='aed'>({R['cprdv']:.0f} AED)</span>" if R['cprdv'] else "<span class='none'>—</span>"
    cpl_disp=f"{eur(r['spend']/lead):.0f} € <span class='aed'>({r['spend']/lead:.0f} AED)</span>" if lead else "<span class='none'>—</span>"
    notes=" ".join(x for x in [R['crea'],R['life']] if x)
    isely='ely' in r['ad'].lower()
    pilot_rows.append(f"""<tr class="pr {R['cls']}">
<td class="adname">{'🎯 ' if isely else ''}{html.escape(r['ad'])}</td>
<td class="r">{eur(r['spend']):.0f} €<span class="aed">{r['spend']:.0f} AED</span></td>
<td class="r">{num(r['impr'])}</td><td class="r">{r['ctr']:.2f}%</td><td class="r hook">{r['v3hookpct']:.0f}%</td>
<td class="r">{num(r['lpv'])}</td><td class="r strong">{lead}</td><td class="r cprdv">{cpl_disp}</td>
<td class="r strong">{rdv}</td><td class="r cprdv">{cprdv_disp}</td>
<td><span class="tag {R['cls']}">{R['tag']}</span><div class="reco">{html.escape(R['act'])}{(' <b>'+html.escape(notes)+'</b>') if notes else ''}</div></td></tr>""")

# ---------- historical ----------
def cpl_cls(v):
    if v is None: return 'none'
    return 'good' if v<=8 else ('mid' if v<=15 else 'bad')
def vcr_cls(v):
    if v is None: return 'none'
    return 'good' if v>=15 else ('mid' if v>=8 else 'bad')
hist_rows=[]
for a in ads:
    cprdv_e=a['cprdv_eur']
    if a['rdv']==0: cls='none'; disp='—'
    else:
        cls='good' if cprdv_e<=20 else ('mid' if cprdv_e<=35 else 'bad'); disp=f"{cprdv_e:.1f} € <span class='aed'>({num(a['cprdv'])} AED)</span>"
    win='★' if (a['rdv']>=3 and cprdv_e is not None and cprdv_e<=acct_cprdv_eur) else ''
    cpl_disp=f"{a['cpl_eur']:.1f} €" if a['cpl_eur'] is not None else "—"
    vcr_disp=f"{a['vcr']:.1f}%" if a['vcr'] is not None else "—"
    hist_rows.append(f"""<tr data-spend="{a['spend']}" data-rdv="{a['rdv']}" data-cprdv="{a['cprdv_eur'] or 999999}" data-ctr="{a['ctr']}" data-hook="{a['hook']}" data-cpl="{a['cpl_eur'] or 999999}" data-vcr="{a['vcr'] or -1}" data-name="{html.escape(a['ad']).lower()}">
<td class="adname">{'<span class=star>★</span> ' if win else ''}{html.escape(a['ad'])}<div class="camp">{html.escape(a['campaigns'])}</div></td>
<td class="r">{a['spend_eur']:.0f} €<span class="aed">{num(a['spend'])} AED</span></td>
<td class="r">{num(a['impr'])}</td><td class="r">{a['ctr']:.2f}%</td><td class="r hook">{a['hook']:.0f}%</td>
<td class="r">{a['vsl']}</td><td class="r {cpl_cls(a['cpl_eur'])}">{cpl_disp}</td>
<td class="r strong">{a['rdv']}</td><td class="r cprdv {cls}">{disp}</td><td class="r {vcr_cls(a['vcr'])}">{vcr_disp}</td></tr>""")

by_rdv=sorted([a for a in ads if a['rdv']>0],key=lambda x:x['rdv'],reverse=True)[:10]; maxr=max((a['rdv'] for a in by_rdv), default=1)
bars=''.join(f"""<div class="barrow"><div class="barlabel">{html.escape(a['ad'])}</div><div class="bartrack"><div class="bar" style="width:{a['rdv']/maxr*100:.1f}%"></div><span class="barval">{a['rdv']} RDV · {a['cprdv_eur']:.0f} €/RDV</span></div></div>""" for a in by_rdv)
winners=sorted([a for a in ads if a['rdv']>=3],key=lambda x:x['cprdv'])[:6]
wcards=''.join(f"""<div class="wcard"><div class="wname">{html.escape(a['ad'])}</div><div class="wbig">{a['cprdv_eur']:.1f} €<span>/RDV</span></div><div class="wsub">{a['rdv']} RDV · {a['spend_eur']:.0f} € · CTR {a['ctr']:.2f}% · Hook {a['hook']:.0f}%</div></div>""" for a in winners)

CSS=open('dash_css.txt').read()
H=f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dashboard Ads — Académie Excellence</title><style>{CSS}</style></head><body>
<div class="head"><div><h1>⚽ Dashboard Publicités — Académie Excellence</h1><div class="sub">Compte <b>Valentin Barreaux_Coaching</b> · Monitoring temps réel · Pilotage + Benchmark + Historique</div></div>
<div style="text-align:right"><div class="badge">Mis à jour : {today}</div><div class="badge" style="margin-top:6px">1 AED = 0,238 €</div></div></div>

<h2 class="s1" style="margin-top:24px">📐 BENCHMARK — Funnel VSL de référence (frères Teliosa) vs tes chiffres</h2>
{benchpanel}

<div class="section-pilot">
<h2 class="s1">🎯 PILOTAGE — Ads actives (7 derniers jours)</h2>
<div class="sub2">{len(act)} ads ont diffusé · {eur(s7):.0f} € ({num(s7)} AED) · <b>{lead7} prospects</b> ({eur(cpl7):.0f} €/prospect) · {num(lpv7)} vues landing · {rdv7} RDV ({eur(cprdv7):.0f} €/RDV). 🎯 = ads Ely.</div>
<div class="chips">{chips}</div>
<div class="note" style="margin-top:0;margin-bottom:12px"><b>ℹ️ Event « Prospect » (lead) branché.</b> Les colonnes <b>Prospects</b> et <b>Coût/prospect</b> viennent de ton pixel lead Meta (« coût par prospect »). À vérifier : si prospects ≈ RDV, le pixel se déclenche <b>près de la réservation (questionnaire)</b> plutôt qu'à l'opt-in du haut de tunnel — si ce n'est pas voulu, contrôle son emplacement.</div>
<div class="tablewrap"><table class="pilot"><thead><tr><th>Ad active</th><th class="r">Dépense 7j</th><th class="r">Impr.</th><th class="r">CTR</th><th class="r">Hook</th><th class="r">Vues landing</th><th class="r">Prospects</th><th class="r">Coût/prospect</th><th class="r">RDV</th><th class="r">Coût/RDV</th><th>Reco d'action</th></tr></thead><tbody>{''.join(pilot_rows)}</tbody></table></div>
<div class="note gold"><b>💡 Répliquer les superwinners :</b> pour chaque ad « Scaler » ou « Pépite », crée 2–3 variantes proches (même angle/hook) et teste-les — c'est comme ça qu'on va chercher du reach en gardant l'efficacité.</div>
</div>

<h2>📈 KPI globaux (lifetime)</h2>
<div class="kpis">
<div class="kpi"><div class="lab">Dépense totale</div><div class="val">{eur(T['spend']):,.0f} € <small>/ {num(T['spend'])} AED</small></div></div>
<div class="kpi"><div class="lab">RDV générés</div><div class="val">{T['rdv']:.0f}</div></div>
<div class="kpi"><div class="lab">Leads (opt-in VSL)</div><div class="val">{tot_lead}</div></div>
<div class="kpi"><div class="lab">CPL moyen</div><div class="val">{(f"{acc['cpl']:.2f} €" if acc['cpl'] else "—")} <small>cible 5–15 €</small></div></div>
<div class="kpi"><div class="lab">VCR moyen</div><div class="val">{(f"{acc['vcr']:.1f}%" if acc['vcr'] else "—")} <small>cible ~15–20%</small></div></div>
<div class="kpi"><div class="lab">Coût/RDV moyen</div><div class="val">{acct_cprdv_eur:.1f} € <small>/ {acct_cprdv_aed:.0f} AED</small></div></div>
</div>

<h2>🏆 Superwinners historiques — meilleur coût/RDV (≥ 3 RDV)</h2>
<div class="wcards">{wcards}</div>

<div class="grid2" style="margin-top:24px">
<div class="panel"><h3>Top 10 créatives par volume de RDV (lifetime)</h3>{bars}</div>
<div class="panel"><h3>Prochaine étape — ROAS réel</h3><p class="ptxt">Cette vue couvre Meta jusqu'au RDV. Pour le <b>coût par vente</b>, le <b>ROAS par ad</b> et compléter les étapes Call/Client du benchmark, on branche ton CRM (crm.valentinbarreaux.com).</p></div>
</div>

<h2>📊 Historique complet — toutes les créatives ({len(ads)})</h2>
<div class="tabhead"><div class="legend">Trier : clic sur l'en-tête · <b>CPL</b> cible 5–15 € (<span class="good">vert</span>≤8 · <span class="mid">jaune</span>≤15 · <span class="bad">rouge</span>&gt;15) · <b>VCR</b> cible ~15% (<span class="good">vert</span>≥15% · <span class="mid">jaune</span>≥8%)</div><input class="search" id="s" placeholder="Rechercher une ad…" oninput="filt()"></div>
<div class="tablewrap"><table id="t"><thead><tr>
<th onclick="srt('name')">Créative / Campagne</th><th onclick="srt('spend')" class="r">Dépense</th><th onclick="srt('impr')" class="r">Impr.</th><th onclick="srt('ctr')" class="r">CTR</th><th onclick="srt('hook')" class="r">Hook</th><th class="r">Leads</th><th onclick="srt('cpl')" class="r">CPL</th><th onclick="srt('rdv')" class="r">RDV</th><th onclick="srt('cprdv')" class="r">Coût/RDV</th><th onclick="srt('vcr')" class="r">VCR</th></tr></thead><tbody id="tb">{''.join(hist_rows)}</tbody></table></div>

<div class="foot">Extraction automatique via l'API Meta Ads. Lead = event « Prospect ». CPL = dépense ÷ leads. VCR = RDV ÷ leads. RDV = « Completed SS Application ». Benchmark = funnel VSL frères Teliosa. Recos = suggestions basées sur tes chiffres (cible coût/RDV ≈ {acct_cprdv_eur:.0f} €). Taux AED→EUR du {today}.</div>
<script>
const tb=document.getElementById('tb');let dir={{}};
function srt(k){{const rows=[...tb.querySelectorAll('tr')];if(dir[k]===undefined){{dir[k]=(k==='name');}}else{{dir[k]=!dir[k];}}const asc=dir[k];
rows.sort((a,b)=>{{let x,y;if(k=='name'){{x=a.dataset.name;y=b.dataset.name;return asc?x.localeCompare(y):y.localeCompare(x);}}x=+a.dataset[k];y=+b.dataset[k];return asc?x-y:y-x;}});rows.forEach(r=>tb.appendChild(r));}}
function filt(){{const q=document.getElementById('s').value.toLowerCase();tb.querySelectorAll('tr').forEach(r=>{{r.style.display=r.dataset.name.includes(q)?'':'none';}});}}
srt('rdv');
</script></body></html>"""
open('dashboard_ads.html','w').write(H)
print("written",len(H),"bytes · CPL acct",round(acc['cpl'],2) if acc['cpl'] else None,"€ · VCR acct",round(acc['vcr'],1) if acc['vcr'] else None,"%")
