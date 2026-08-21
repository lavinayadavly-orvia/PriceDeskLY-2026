import json,re,sys
s=open('dist/index.html',encoding='utf-8').read()
fail=[];warn=[];ok=[]
def chk(c,m): (ok if c else fail).append(m)

# --- document integrity ---
chk(s.startswith('<!doctype html>'),"standalone doctype")
chk('<meta charset="utf-8">' in s,"charset declared")
chk('name="robots" content="noindex,nofollow,noarchive"' in s,"noindex for internal data")
chk('rel="icon"' in s,"favicon present")
chk(s.count('<html')==1 and s.count('</html>')==1,"single well-formed html element")

# --- data integrity ---
T=json.loads(re.search(r'const TASKS = (\[.*?\]);',s,re.S).group(1))
chk(len(T)==122,f"122 tasks ({len(T)})")
chk(len({t['id'] for t in T})==len(T),"task ids unique")
bad=[t['task'] for t in T if t['kind']=='hours' and
     abs(((t['fte'] or 0)*t['frate']+(t['rev'] or 0)*t['rrate'])-t['unit'])>1e-6]
chk(not bad,f"unit costs recompute from hours x rates ({len(bad)} bad)")
chk(all(t['unit']>=0 for t in T),"no negative unit costs")

# --- pricing rules encoded ---
chk("t.kind!=='hours'?0:" in s,"pass-through carries zero margin structurally")
chk('Math.round(m<1?u/(1-m):u)' in s,"unit price rounded so qty x price ties out")
chk('MARGIN_FLOOR=22.5' in s,"22.5% floor constant present")
chk('contingenc' not in s.lower(),"no contingency anywhere in the model")
chk('profGross=svcPrice' in s,"quote total is the sum of line prices")

# --- theme system ---
css=s.split('</style>')[0]
root=re.search(r':root\{(.*?)\}',css,re.S).group(1)
base={m.group(1) for m in re.finditer(r'(--[a-z0-9-]+)\s*:',root)}
dark=set()
for blk in re.findall(r':root(?::not\(\[data-theme="light"\]\))?\[?[^{]*\{(.*?)\}',css,re.S):
    dark|={m.group(1) for m in re.finditer(r'(--[a-z0-9-]+)\s*:',blk)}
chk(not (dark-base),f"no token defined only in a dark block ({sorted(dark-base)})")
chk('@media (prefers-color-scheme:dark)' in css,"system dark handled")
chk(':root[data-theme="dark"]' in css,"explicit dark stamp handled")
chk(':root:not([data-theme="light"])' in css,"explicit light beats OS dark")
chk('body{margin:0;background:var(--ground)' in css.replace('\n',''),"body paints a token background")

# --- palette is the requested one ---
chk('--ground:#dfedf4' in css,"powder blue ground")
chk('--ink:#000000' in css,"black font in light theme")
chk('--brand:#e8730a' in css,"tangerine accent")
chk('--brand-ink:#000000' in css,"black label on tangerine fills")

# --- features present ---
for name,marker in [("templates store",'pricedeskly.templates.v2'),("folders",'tplFolderAdd'),
                    ("scenarios",'pricedeskly.scenarios.v1'),("autosave",'pricedeskly.working.v1'),
                    ("share link",'scenShare'),("client quote",'pane-quote'),
                    ("discount solver",'reqMargin'),("theme toggle",'bTheme')]:
    chk(marker in s,f"feature: {name}")

# --- accessibility ---
inputs=re.findall(r'<input[^>]*>',s)
unl=[i for i in inputs if 'aria-label' not in i and 'id=' not in i and 'type="checkbox"' not in i]
chk(not unl,f"all free inputs labelled ({len(unl)} unlabelled)")
chk(':focus-visible' in css,"visible focus state")
chk('overflow:auto' in css,"wide content scrolls in-container")

print(f"PASS {len(ok)}")
for m in ok: print("  +",m)
if fail:
    print(f"FAIL {len(fail)}")
    for m in fail: print("  -",m)
else: print("FAIL 0")
sys.exit(1 if fail else 0)
