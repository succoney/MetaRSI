"""Read-only held-out result collection. Keep first evaluations separate from rerun replacements."""
import subprocess,json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];(ROOT/'evidence').mkdir(exist_ok=True)
PRE='''import json,hashlib\nfrom pathlib import Path\nsources=[]\ndef read(path):\n p=Path(path);raw=p.read_bytes();sources.append(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest()));return json.loads(raw)\n'''
SNIPPETS={
'mini':('10.11.1.29',r'''
d=read('/data/jyx/FlashRSI/runs/tb21-rrsi-deepseek/heldout-20261108-125145/comparison.json');a=d['evaluations']['baseline'];b=d['evaluations']['final'];n=len(d['per_task']);out=dict(tasks=n,repeats=1,baseline_id=a['snapshot_id'],best_id=b['snapshot_id'],original=dict(baseline_passed=round(a['test_score']*n),best_passed=round(b['test_score']*n)),revised=None,note='首次独立测试；无替换重测记录。',sources=sources)
'''),
'claude':('174.1.59.1',r'''
d=read('/data/dlx/flashrsi_tb21_claude_initial_test_20261111/reports/baseline_vs_round5.json');c=read('/data/dlx/flashrsi_tb21_env_repair_20261111/reports/corrected_comparison.json');a=c['versions']['v0'];b=c['versions']['v1'];out=dict(tasks=d['test_tasks'],repeats=1,baseline_id=d['baseline_snapshot_id'],best_id=d['best_snapshot_id'],original=dict(baseline_passed=d['baseline_passed'],best_passed=d['best_passed']),revised=dict(baseline_passed=a['passed'],best_passed=b['passed'],baseline_retests=a['retested_tasks'],best_retests=b['retested_tasks'],type='confirmed_environment_retest'),note='重测后：仅替换已确认的环境故障，基线 5 题、进化版本 4 题；保留首次结果。',sources=sources)
'''),
'tree':('10.11.1.31',r'''
r='/data/cwl/FlashRSI/runs/tree-rsi-tb21-30-59/';a=read(r+'test-h0-baseline-20261111/summary.json');b=read(r+'retry-c15-test-errors-20261111/test-summary-with-reruns.json');old=b['original_test_summary'];new=b['test_summary_with_reruns'];out=dict(tasks=a['n_tasks'],repeats=1,baseline_id=a['snapshot_id'],best_id=b['snapshot_id'],original=dict(baseline_passed=a['n_passed'],best_passed=old['n_passed']),revised=dict(baseline_passed=a['n_passed'],best_passed=new['n_passed'],type=b['mode']),note='重测后：最终 C15 使用诊断重测替换汇总；基线 H0 保留原始测试。与 Claude Code 的环境修复重测口径不同。',sources=sources)
''')}
out={}
for key,(host,code) in SNIPPETS.items():
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','root@'+host,'python3 -'],input=PRE+code+'\nprint(json.dumps(out,ensure_ascii=False))\n',text=True,capture_output=True,check=True)
 d=json.loads(p.stdout);d['server']=host;d['retrieved_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();out[key]=d
 print(key,d['original'],'revised',d['revised'])
(ROOT/'evidence/test-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
