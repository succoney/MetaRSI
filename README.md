# meta-rsi

**打造垂域专属 Harness，让智能体进化出领域专长。**

组合 Harness、Model、Method 与 Dataset，通过真实任务反馈迭代执行规则、工具和技能。主页展示每轮候选、正确率、父子关系与选择结果，并支持下载所选节点的真实 Harness 文件。

## 查看主页

直接打开 `dist/index.html`，或在本目录运行：

```sh
python3 -m http.server 8080 --directory dist
```

## 真实实验数据

2026 年 11 月 11 日从三台服务器通过只读 SSH 采集，页面展示采集时刻。未改变、重启或补跑任何实验。

| 组合 | 来源 | 基线 | 历史最优 | 完成轮数 |
|---|---|---:|---:|---:|
| MiniAgent / DeepSeek / RRSI | .29 | 73.33% | 91.67% | 12 |
| Claude Code / DeepSeek / RRSI | .1 | 75.00% | 81.67% | 5 |
| MiniAgent / DeepSeek / TreeRSI | .31 | 78.33% | 88.33% | 5 |

TreeRSI 的完整运行包含 16 个节点（基线及 15 个候选）。多分支使用原始 `parent_id` 连线，逐轮束选择读取 `tree-state.json` 的 `selected_ids`。节点进入树不等于进入当前搜索束；页面分别呈现。第 3 轮有真实 0 分候选，保留分数及执行错误数，不移除失败分支。

共同口径：Terminal-Bench 2.1，30 个进化任务，每题重复 2 次，共 60 次正式评估；不包含 smoke 预检查。分数来自进化检查点，不是独立测试成绩，也未混入后续环境修复重测结果。

MiniAgent 第 13 轮包含已生成但无完整评分的候选。第 7、8 轮没有带有效 snapshot 的候选，按原始记录保留为空；不会补造分数、节点或改动。原运行存在中断记录，页面是历史回放，不声称服务器实验仍在运行。

数据来源：

- .29：`/data/jyx/FlashRSI-worktrees/rrsi-efficient/runs/tb21-rrsi-deepseek-resume-round6-20261108-191938/rrsi-miniagent-terminal_bench-20261108-192004-800306`
- .31：`/data/cwl/FlashRSI/runs/tree-rsi-tb21-30-59/tree_rsi-miniagent-terminal_bench-20261110-014335-979851`
- .1：`/data/dlx/flashrsi_tb21_claude_20261109/runs/evolution/rrsi-claude_code-terminal_bench-20261110-153859-703989`

RRSI 以 `checkpoints/round.json` 的原生 history、scores 与 phases/proposal 为依据，按轮次、variant、snapshot 合并组件级记录。候选正确率由父轮得分加原生 delta_S 得出。`results.json` 保留完整 snapshot ID、父节点、选择依据、文件改动和检查点 SHA-256；ZIP 内附来源记录。

## 独立测试结果

各组为 Terminal-Bench 2.1 的 59 个测试任务、每题 1 次。默认“当前结果”中，Claude Code 使用环境修复后的 66.10% → 69.49%，TreeRSI 使用重测后的 67.80% → 79.66%（40/59 → 47/59），MiniAgent / RRSI 保持首次结果。另可切换查看全部首次测试或包含重测替换的汇总。

| 组合 | 首次基线 | 首次进化版本 | 重测后基线 | 重测后进化版本 |
|---|---:|---:|---:|---:|
| MiniAgent / RRSI | 38/59 · 64.41% | 43/59 · 72.88% | 无替换重测 | 无替换重测 |
| Claude Code / RRSI | 34/59 · 57.63% | 37/59 · 62.71% | 39/59 · 66.10% | 41/59 · 69.49% |
| MiniAgent / TreeRSI | 40/59 · 67.80% | 45/59 · 76.27% | 原始 H0：40/59 · 67.80% | 47/59 · 79.66% |

Claude Code 重测仅替换已确认环境故障：v0 5 题、v1 4 题。TreeRSI 使用 C15 的诊断重测替换汇总，H0 保持原始结果；两者口径不同。三组的实验环境、基线测量不同，不能当作严格控制变量的方法排名。测试集不进入进化曲线，也不用于选择回放中的候选。

测试源文件路径与 SHA-256 保存在每组 `test_results.sources`，页面可展开或下载查阅。原始结果全部保留；本次未发起任何重测。

## 页面交互

- 深蓝、紫色与冰青配色；去掉组件之间的加号横条。
- 首屏曲线绘制、浮动面板、滚动出现、节点入场动效；尊重系统减少动态效果设置。
- 三组真实实验可切换；Part 3 支持播放、暂停、重播、上一轮、下一轮、进度拖动和 1× / 2× / 4× 速度。
- 回放分为候选生成与评估完成两步，逐轮加入节点和分数；未评估候选保持待定。
- 点击曲线点或树节点，查看真实父节点、采纳决定、改动路径、原始修改依据和 diff。
- 下载真实 Harness ZIP：包含 `harness/` 文件、原始 `snapshot.json` 和 `provenance.json`，保留可执行权限。按相应 Harness 接口使用；不包含运行环境或模型服务。
- 配置区生成并下载新实验配置；数据集仅本地选择，不上传，不触发远程任务。配置区与历史运行相互独立。

## 更新数据

在能访问对应服务器且具备既有 SSH 权限的环境执行：

```sh
python3 scripts/collect_results.py
python3 scripts/collect_tree_results.py
python3 scripts/collect_test_results.py
python3 scripts/prepare_data.py
```

采集脚本只读取检查点和快照，不写入服务器、不读取认证文件。前端无服务端账号或 API 密钥。`evidence/` 保存本地采集证据；前端只使用 `dist/` 中的展示数据与下载包。更新实验时先修改脚本中的明确运行目录，不混合不同实验口径。

## GitHub Pages

将本目录作为仓库根目录，Settings → Pages → Build and deployment 选择 GitHub Actions。在 Actions 中手动运行 `Deploy product homepage` 工作流即可部署 `dist/`。工作流不在推送时自动发布。放入已有仓库子目录时需调整上传路径。

## 验证

- JavaScript 语法、页面资源与锚点、数据范围、父子节点、60 次评估分母、最优分数一致性检查通过。
- 独立 Chrome 浏览器验证三组数据回放、候选生成期间不显示评分、未完成候选限制、节点与曲线点击、快照 ZIP 下载。
- TreeRSI 每轮候选无位置重叠，第二轮 3 个束选择与最终 16 节点结果一致；首次测试 / 重测汇总切换与真实 ZIP 下载通过。
- 桌面 1440px 与手机 390px 布局检查通过，手机无页面级横向溢出；无 JavaScript 运行时异常。

项目仓库：[succoney/MetaRSI](https://github.com/succoney/MetaRSI)。基于 FlashRSI 实验记录构建产品展示。

图表默认聚焦 baseline 到历史最优附近的区间（TreeRSI：75–95%），低于范围的候选用可点击向下标记呈现，并可切换 0–100% 完整范围。详情、代码区及页面使用统一的深色细滚动条。
