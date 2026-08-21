import json,re
RATE={'Medical':950,'SSU':800,'DM':850,'PM':1350,'SM':1100,'EC':1200,'BioStats':1200}
REV=3000
D_SITE='site'; D_FIX='fixed'; D_VISIT='visit'; D_MONTH='month'; D_SM='sitemonth'
D_WEEK='week'; D_PAT='patient'; D_MV='mvisit'; D_MAN='manual'

# driver overrides: dept -> {task-prefix: driver}. default fixed.
OV={
'SSU':{'Site Identification':D_SITE,'Pre-feasibility form development':D_FIX,'Pre-feasibility':D_SITE,
 'Feasibility Report':D_FIX,'Feasibility':D_SITE,'Essential document collection':D_SITE,
 'PSQV':D_SITE,'CSA/MoU development':D_FIX,'CSA/MoU negotiation':D_SITE,'EC Dossier':D_SITE,
 'EC Communication':D_SITE,'Finance & Admin':D_SITE,'SIV Dossier':D_SITE,'Site Handover':D_SITE,
 'TMF Support':D_SITE,'ISF Support':D_SITE,'eISF support':D_SITE},
'DM':{'Data Digitization':D_VISIT,'Trackers update':D_MONTH,'Data QC':D_VISIT,'Query generation':D_VISIT,'Query resolution':D_VISIT},
'PM':{'TMF Management':D_SITE,'Study Progress Calls':D_SM,'Client calls weekly':D_WEEK,'Vendor Management':D_FIX},
'SM':{'Daily follow-up':D_SM,'Documentation':D_SM,'EDC verification':D_SITE,'Query resolutions':D_SITE,
 'Site re-training':D_SITE,'SIV preparation':D_SITE,'SIV':D_SITE,'SMV preparation':D_MV,'SMV':D_MV,
 'SCV Preparation':D_SITE,'SCV':D_SITE,'Local travel':D_MV,'Out-station travel':D_MV},
'EC':{'Client Communications':D_MONTH,'Coordination with PM':D_MONTH},
}
def driver(dept,task):
    for k,v in sorted(OV.get(dept,{}).items(), key=lambda kv:-len(kv[0])):
        if task.startswith(k): return v
    return D_FIX

SKIP={'Prospective study','Retrospective study'}
tasks=[];i=0
for line in open('data/rate_card_raw.tsv').read().splitlines()[1:]:
    p=line.split('\t')
    dept,task,rate,fte,revrate,rev = p[0],p[1],p[2],p[3],p[4],p[5]
    if task in SKIP: continue
    i+=1
    fh = None if fte.strip() in ('','NA') else float(fte)
    rh = 0.0 if rev.strip() in ('','NA') else float(rev)
    fr = RATE[dept]
    unit = (fh or 0)*fr + rh*REV
    notset = (fh is None and rh==0)
    tasks.append(dict(id=f"t{i}",dept=dept,task=task,driver=driver(dept,task),
        fte=fh, rev=rh, frate=fr, rrate=REV, unit=round(unit,2),
        kind='hours', notset=notset))

# Pass-through & Tech: unit-priced, no hours
PT=[('PTC','ICD Translation & back translations',D_MAN,20000),
('PTC','Ethics Committee Fee - Institutional',D_SITE,100000),
('PTC','Ethics Committee Fee - Central',D_SITE,20000),
('PTC','Travel - Local',D_MAN,2500),
('PTC','Travel - Out of Station',D_MAN,20000),
('PTC','Boarding & lodging',D_MAN,10000),
('PTC','Printing & Courier',D_MAN,2000),
('PTC','External CRC',D_SM,30000),
('PTC','External Data entry operator',D_MAN,20000),
('PTC','Journal Fee',D_FIX,None),
('PTC','PI Fee / Data record Fee (per patient)',D_PAT,4000),
('PTC','Data entry Fee (per patient)',D_PAT,None),
('PTC','Institutional Overhead',D_SITE,None),
('Tech','EDC Monthly License Fee',D_MONTH,None),
('Tech','MEDDRA License Fee',D_FIX,None),
('Tech','QoL/PRO License Fee',D_FIX,None),
('Tech','eTMF monthly license Fee',D_MONTH,None),
('Tech','eISF monthly license Fee',D_MONTH,None)]
for dept,task,drv,unit in PT:
    i+=1
    tasks.append(dict(id=f"t{i}",dept=dept,task=task,driver=drv,fte=None,rev=0,
        frate=None,rrate=None,unit=unit if unit is not None else 0,
        kind='passthrough' if dept=='PTC' else 'tech', notset=unit is None))

open('data/tasks.json','w').write(json.dumps(tasks,separators=(',',':')))
h=[t for t in tasks if t['kind']=='hours']
print("tasks:",len(tasks)," hour-based:",len(h)," rate-not-set:",sum(1 for t in tasks if t['notset']))
from collections import Counter
print("by dept:",dict(Counter(t['dept'] for t in tasks)))
print("by driver:",dict(Counter(t['driver'] for t in tasks)))
for chk,exp in [('Concept Note Writing',30200),('Protocol Writing -Post Marketing/RWE',120500),
                ('Trackers update',31275),('Client calls weekly',62700),('Site Identification (per site)',400),
                ('Daily follow-up',275),('Registration',12000)]:
    got=[t['unit'] for t in tasks if t['task']==chk]
    print(f"  check {chk:42} got={got[0]:>10,.0f} expect={exp:>10,.0f} {'OK' if abs(got[0]-exp)<1 else 'MISMATCH'}")
