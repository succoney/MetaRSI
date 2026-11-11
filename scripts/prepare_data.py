import json,base64,zipfile,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';(OUT/'artifacts').mkdir(exist_ok=True)
all_data={}
test_results=json.loads((ROOT/'evidence/test-results.json').read_text()) if (ROOT/'evidence/test-results.json').exists() else {}
for key in ['mini','claude','tree']:
 d=json.loads((ROOT/'evidence'/f'{key}.json').read_text()); snapshots=d.pop('snapshots'); nodes=[dict(id=d['baseline_id'],parent=None,round=0,variant=0,score=d['baseline'],accepted=True,reason='原始基线',changes=[],diff='',complete=True)]+d.pop('candidates')
 for n in nodes:
  n['label']='Baseline' if n['round']==0 else f"R{n['round']:02d} · C{n['variant']}"
  paths=list(dict.fromkeys(p for c in n['changes'] for p in (c.get('paths') or [])))
  n['paths']=paths
  n['title']='初始执行方案' if not n['round'] else ' / '.join(dict.fromkeys({'prompt':'提示规则','skill':'技能','hook':'执行钩子','config':'运行配置','code':'执行逻辑','control_flow':'执行控制','tool':'工具','agent':'子代理','subagent':'子代理','context_mgmt':'上下文管理','client_tool':'客户端工具'}.get(c.get('component'),c.get('component') or '资源') for c in n['changes']))
  n['artifact']=None;n['file_count']=0
  if n['id'] in snapshots:
   snap=snapshots[n['id']]; n['file_count']=len(snap['files']); name=f"{key}-{n['label'].replace(' · ','-').lower()}.zip";n['artifact']='artifacts/'+name
   with zipfile.ZipFile(OUT/'artifacts'/name,'w',zipfile.ZIP_DEFLATED) as z:
    for path,f in snap['files'].items():
     assert not Path(path).is_absolute() and '..' not in Path(path).parts
     content=base64.b64decode(f['content']); text=content.decode(errors='replace')
     assert not re.search(r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|sk-[a-zA-Z0-9]{30,}|art_v2_[a-zA-Z0-9_]{20,}',text),'Sensitive value detected'
     info=zipfile.ZipInfo('harness/'+path);info.external_attr=(0o100755 if f.get('executable') else 0o100644)<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,content)
    z.writestr('snapshot.json',json.dumps(snap,ensure_ascii=False,indent=2))
    z.writestr('provenance.json',json.dumps({k:d[k] for k in ['server','run_dir','retrieved_at','checkpoint_sha256','dataset','tasks','repeats']}|{'node':n},ensure_ascii=False,indent=2))
 d['test_results']=test_results.get(key);
 if d['test_results']:
  assert d['test_results']['baseline_id']==d['baseline_id']
  assert d['test_results']['best_id']==d['best_id']
 d['nodes']=nodes;d['total_rounds']=max(d['completed_rounds'],max(n['round'] for n in nodes));all_data[key]=d
(OUT/'results.js').write_text('window.META_RSI_RESULTS = '+json.dumps(all_data,ensure_ascii=False)+';\n')
(OUT/'results.json').write_text(json.dumps(all_data,ensure_ascii=False,indent=2))
print('Prepared verified data:',[(k,len(d['nodes']),d['total_rounds']) for k,d in all_data.items()])
