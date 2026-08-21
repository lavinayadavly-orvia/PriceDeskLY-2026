import json,re,sys
s=open('PriceDeskLY.html',encoding='utf-8').read()
fail=[];warn=[];ok=[]
def chk(c,msg): (ok if c else fail).append(msg)

# 1 data integrity
T=json.loads(re.search(r'const TASKS = (\[.*?\]);',s,re.S).group(1))
chk(len(T)==122,f"task count = {len(T)}")
chk(len({t['id'] for t in T})==len(T),"task ids unique")
bad=[t['task'] for t in T if t['kind']=='hours' and
     abs(((t['fte'] or 0)*t['frate']+(t['rev'] or 0)*t['rrate'])-t['unit'])>1e-6]
chk(not bad,f"all hour-based unit costs recompute from hours x rates ({len(bad)} bad)")
nonint=[(t['task'],t['unit']) for t in T if abs(t['unit']%1)>1e-9]
chk(not nonint,f"no fractional unit costs ({nonint[:3]})")
chk(all(t['unit']>=0 for t in T),"no negative unit costs")
drivers={t['driver'] for t in T}
known={'fixed','site','visit','month','sitemonth','week','vendormonth','mvisit','patient','manual'}
chk(drivers<=known,f"drivers within known set (extra: {drivers-known})")
ns=[t['task'] for t in T if t['notset']]
chk(all(t['unit']==0 for t in T if t['notset']),"rate-not-set rows priced at 0")
ok.append(f"rate-not-set rows = {len(ns)}")

# 2 every id used in JS exists in markup
ids=set(re.findall(r'id="([A-Za-z0-9_-]+)"',s))
used=set(re.findall(r"\$\('#([A-Za-z0-9_-]+)'\)",s))
chk(used<=ids,f"all $('#id') targets exist (missing: {sorted(used-ids)})")
unused=ids-used-{'tb','wf','q','kpis','deptBars','mixSplit','mixLegend','hourBars','topBars',
                 'baseBars','unitEcon','auditList','deptChips','pane-scope','pane-dash',
                 'pane-bridge','pane-audit'}
if unused: warn.append(f"ids never referenced: {sorted(unused)}")

# 3 theme safety: no color token defined ONLY inside a media/[data-theme] block
css=s.split('</style>')[0]
root=re.search(r':root\{(.*?)\}',css,re.S).group(1)
base={m.group(1) for m in re.finditer(r'(--[a-z0-9-]+)\s*:',root)}
dark=set()
for blk in re.findall(r':root(?:\:not\(\[data-theme="light"\]\))?\[?[^{]*\{(.*?)\}',css,re.S):
    dark|={m.group(1) for m in re.finditer(r'(--[a-z0-9-]+)\s*:',blk)}
orphan=dark-base
chk(not orphan,f"no token defined only in a dark block (orphans: {sorted(orphan)})")
chk('body{margin:0;background:var(--ground)' in css.replace('\n',''),"body paints an explicit token background")

# 4 both dark scopes present
chk('@media (prefers-color-scheme:dark)' in css,"prefers-color-scheme block present")
chk(':root[data-theme="dark"]' in css,"data-theme=dark scope present")
chk(':root:not([data-theme="light"])' in css,"light-stamp guard present")

# 5 formatting consistency: table cells must not emit raw numbers
chk('value="${money(uv)}"' in s,"unit cost rendered through money()")
chk('value="${qtyFmt(qv)}"' in s,"quantity rendered through qtyFmt()")
chk('acct(lp)' in s,"line price rendered through accounting formatter")
chk('value="${(mv*100).toFixed(1)}"' in s,"per-line margin rendered as a percentage")
chk('const marginOf=' in s and 'unitPriceOf' in s,"margin applied at line level")
chk("t.kind!=='hours'?0:" in s,"pass-through lines carry zero margin by construction")
chk('type="number"' not in s.split('<div class="wrap">')[1].split('</aside>')[1],
    "no raw number inputs left in the table")

# 6 accessibility
inputs=re.findall(r'<input[^>]*>',s)
unlabelled=[i for i in inputs if 'aria-label' not in i and 'id=' not in i and 'type="checkbox"' not in i]
chk(not unlabelled,f"every free input labelled ({len(unlabelled)} unlabelled)")
chk(':focus-visible' in css,"visible focus state defined")
chk('overflow:auto' in css or 'overflow-x:auto' in css,"wide content scrolls in its own container")

print("PASS")
for m in ok: print("  +",m)
if warn:
    print("WARN")
    for m in warn: print("  ~",m)
print("FAIL" if fail else "FAIL  (none)")
for m in fail: print("  -",m)
sys.exit(1 if fail else 0)
