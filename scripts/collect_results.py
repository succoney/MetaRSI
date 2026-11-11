"""Read only: collect whitelisted experiment evidence over SSH; never run experiments."""
import json,subprocess,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'evidence').mkdir(exist_ok=True)
RUNS={
 'mini':('root@10.11.1.29','/data/jyx/FlashRSI-worktrees/rrsi-efficient/runs/tb21-rrsi-deepseek-resume-round6-20261108-191938/rrsi-miniagent-terminal_bench-20261108-192004-800306','MiniAgent'),
 'claude':('root@174.1.59.1','/data/dlx/flashrsi_tb21_claude_20261109/runs/evolution/rrsi-claude_code-terminal_bench-20261110-153859-703989','Claude Code')}
CODE=r'''
import json,hashlib
from pathlib import Path
from collections import defaultdict
r=Path(RUN_PATH)
p=r/'checkpoints/round.json'; raw=p.read_bytes(); s=json.loads(raw)['data']['state']
groups=defaultdict(list)
for h in s['history']:
 if h.get('candidate_id'):groups[(h['t'],h['variant'],h['candidate_id'])].append(h)
cs=[]
for (t,v,cid), hs in sorted(groups.items()):
 h=hs[0]; delta=h.get('delta_S'); score=s['scores'][t]+delta if delta is not None else None
 cs.append(dict(id=cid,parent=h.get('parent_id'),round=t+1,variant=v+1,score=score,accepted=h.get('accepted'),reason=h.get('reason'),changes=[{k:e.get(k) for k in ['component','paths','operation','hypothesis']} for e in hs],diff=h.get('diff',''),source='checkpoints/round.json',complete=True))
known={c['id'] for c in cs}
for p in sorted((r/'checkpoints/phases').glob('*.json')):
 d=json.loads(p.read_text()).get('data',{}); k=d.get('key',{}); result=d.get('result')
 if k.get('phase')=='proposal' and isinstance(result,list) and len(result)>=2 and isinstance(result[0],str) and result[0] not in known:
  cs.append(dict(id=result[0],parent=k.get('parent'),round=k['step']+1,variant=k['variant']+1,score=None,accepted=None,reason='候选已生成，检查点尚无完整正式评分与选择结果',changes=[{a:e.get(a) for a in ['component','paths','operation','hypothesis']} for e in result[1]],diff='',source=str(p.relative_to(r)),complete=False));known.add(result[0])
cs.sort(key=lambda c:(c['round'],c['variant']))
base=cs[0]['parent']
ids={base,*[c['id'] for c in cs]};snaps={}
for sid in ids:
 p=r/'snapshots'/(sid+'.json')
 if p.exists():
  d=json.loads(p.read_text());snaps[sid]=d
print(json.dumps(dict(baseline=s['baseline_score'],baseline_id=base,best=s['best_score'],best_id=s['best_snapshot_id'],scores=s['scores'],completed_rounds=s['start_step'],candidates=cs,snapshots=snaps,checkpoint_sha256=hashlib.sha256(raw).hexdigest(),run_dir=str(r),error_present=(r/'error.json').exists()),ensure_ascii=False))
'''
all_data={}
for key,(host,run,harness) in RUNS.items():
 code=CODE.replace('RUN_PATH',repr(run))
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=10',host,'python3 -'],input=code,text=True,capture_output=True,check=True)
 d=json.loads(p.stdout);d.update(harness=harness,model='DeepSeek V4.1 Flash',method='RRSI',server=host.split('@')[1],retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),dataset='Terminal-Bench 2.1',tasks=30,repeats=2)
 (ROOT/'evidence'/f'{key}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
 all_data[key]=d
 print(key,'rounds',d['completed_rounds'],'candidates',len(d['candidates']),'baseline',d['baseline'],'best',d['best'],'snapshot keys',list(next(iter(d['snapshots'].values()),{})))
