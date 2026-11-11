"""Read-only TreeRSI collector: preserves native node scores and per-round beam choices."""
import subprocess,json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];(ROOT/'evidence').mkdir(exist_ok=True)
CODE=r'''
from pathlib import Path
import json,hashlib
from collections import Counter
r=Path('/data/cwl/FlashRSI/runs/tree-rsi-tb21-30-59/tree_rsi-miniagent-terminal_bench-20261110-014335-979851')
state_files=sorted((r/'trajectories').glob('*tree-state.json'));states=[json.loads(p.read_text()) for p in state_files];last=states[-1];raw=state_files[-1].read_bytes()
candidates={}
for p in sorted((r/'trajectories').glob('*tree-candidate.json')):
 c=json.loads(p.read_text());candidates[c['candidate_id']]=(c,str(p.relative_to(r)))
base=next(n for n in last['nodes'] if n['parent_id'] is None);cs=[];variants=Counter();snaps={};scores=[base['score']];beam={str(s['step']+1):s['selected_ids'] for s in states}
for n in last['nodes']:
 sid=n['snapshot_id'];p=r/'snapshots'/(sid+'.json')
 if p.exists():snaps[sid]=json.loads(p.read_text())
 if n['parent_id'] is None:continue
 c,source=candidates[sid];rnd=n['round']+1;variants[rnd]+=1
 imp=c.get('implementation',{});attr=c.get('attribution',{});hyp=c.get('hypothesis',{})
 changes=attr.get('component_changes') or [{'component':hyp.get('component_hint','code'),'paths':imp.get('paths',[])}]
 m=c.get('measurement',{});assert m.get('score')==n['score'];assert m.get('n_trials')==60
 cs.append(dict(id=sid,parent=n['parent_id'],round=rnd,variant=variants[rnd],score=n['score'],accepted=sid in beam[str(rnd)],admitted=c.get('admitted'),reason=c.get('reason') or c.get('outcome'),changes=[{'component':e.get('component'),'paths':e.get('paths',[]),'operation':'change','hypothesis':hyp.get('hypothesis','')} for e in changes],diff=imp.get('diff',''),source=source,complete=True,n_trials=m.get('n_trials'),error_trials=m.get('error_trials'),direction=hyp.get('direction'),order=n['order']))
for rnd in range(1,last['step']+2):scores.append(max([base['score']]+[n['score'] for n in cs if n['round']<=rnd]))
result=json.loads((r/'result.json').read_text());best_id=result['snapshot_id'];assert next(n['score'] for n in cs if n['id']==best_id)==max(scores)
print(json.dumps(dict(harness='MiniAgent',model='DeepSeek V4.1 Flash',method='TreeRSI',server='10.11.1.31',dataset='Terminal-Bench 2.1',tasks=30,repeats=2,baseline=base['score'],baseline_id=base['snapshot_id'],best=max(scores),best_id=best_id,scores=scores,completed_rounds=last['step']+1,candidates=cs,snapshots=snaps,beam_by_round=beam,checkpoint_sha256=hashlib.sha256(raw).hexdigest(),checkpoint_source=str(state_files[-1]),run_dir=str(r),error_present=False),ensure_ascii=False))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','root@10.11.1.31','python3 -'],input=CODE,text=True,capture_output=True,check=True)
d=json.loads(p.stdout);d['retrieved_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/'evidence/tree.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print('TreeRSI:',d['baseline'],d['best'],len(d['candidates']),'candidates')
