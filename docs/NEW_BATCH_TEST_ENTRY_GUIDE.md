# 新版批量测试入口使用指南

## 🎯 核心变化

**旧版**: `batch_test.py` - 需要修改代码来调整实验配置  
**新版**: `run_batch_experiments.py` - 完全通过命令行参数控制

---

## 📦 文件清单

新增的核心文件：

```
AutoChip/autochip_scripts/
├── run_batch_experiments.py          # ⭐ 新的批量测试入口
├── api_keys.env                       # ⭐ API Keys配置文件
├── api_keys.env.example               #    配置文件示例
├── BATCH_EXPERIMENTS_GUIDE.md         #    详细使用指南（11KB）
├── PARAMETERIZED_BATCH_TEST_SUMMARY.md #   实施总结报告
├── QUICK_REFERENCE.md                 #    快速参考卡片
└── NEW_BATCH_TEST_ENTRY_GUIDE.md      #    本文件（入口指南）
```

---

## 🚀 5分钟快速上手

### 步骤1: 准备环境（首次使用）

```bash
cd /home/gq/Autochip_workspace/AutoChip/autochip_scripts

# 激活conda环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate autochip

# 检查API Keys配置文件
cat api_keys.env

# 如果需要修改，编辑该文件
nano api_keys.env
```

### 步骤2: 小规模验证（必须！）

```bash
# 测试困难组前3题
python run_batch_experiments.py \
  --group hard \
  --limit 3 \
  --iterations 5 \
  --candidates 2 \
  --mixed-models \
  --env-file api_keys.env \
  --experiment-name my_first_test
```

**预期输出**:
```
================================================================================
AutoChip Parameterized Batch Testing
================================================================================

[OK] Loaded environment variables from: api_keys.env

Preparing test group: HARD
Small-scale test mode: only testing first 3 problems
Problem count: 3
Output directory: outputs/batch_tests/my_first_test_hard_20260414_XXXXXX

Experiment Configuration:
  - Iterations: 5 (will execute 6 times)
  - Candidates: 2
  - Mixed Models: Enabled

[1/3] ... ✅ 完成
[2/3] ... ✅ 完成
[3/3] ... ✅ 完成

HARD Group Test Results
Total:      3
Passed:     X
Pass Rate:  XX.XX%

Results saved to: outputs/batch_tests/my_first_test_hard_*/results_hard.json
```

### 步骤3: 查看结果

```bash
# 查看统计信息
cat outputs/batch_tests/my_first_test_*/results_hard.json | jq '.statistics'

# 查看某个题目的详情
ls outputs/batch_tests/my_first_test_*/Prob050_kmap1/
```

### 步骤4: 全量测试

```bash
# 后台运行，防止SSH断开
nohup python run_batch_experiments.py \
  --group hard \
  --iterations 5 \
  --candidates 3 \
  --mixed-models \
  --env-file api_keys.env \
  --experiment-name full_hard_test \
  > full_hard_test.log 2>&1 &

# 记录进程ID
echo "PID: $!"

# 监控进度
tail -f full_hard_test.log
```

---

## 💡 常用场景速查

### 场景1: 快速验证配置是否正确

```bash
python run_batch_experiments.py \
  -g hard -l 1 -i 2 -k 1 \
  -e api_keys.env \
  -n sanity_check \
  --verbose
```

### 场景2: 对比不同候选数的效果

```bash
# 实验A: 1个候选
python run_batch_experiments.py -g hard -l 10 -i 5 -k 1 -m -e api_keys.env -n k1_test

# 实验B: 3个候选
python run_batch_experiments.py -g hard -l 10 -i 5 -k 3 -m -e api_keys.env -n k3_test

# 对比结果
for f in outputs/batch_tests/k*_test_*/results_hard.json; do
  echo "$(basename $(dirname $f)): $(jq '.statistics.pass_rate' $f)%"
done
```

### 场景3: 禁用混合模型做基线测试

```bash
python run_batch_experiments.py \
  -g hard -l 10 \
  -i 5 -k 2 \
  --no-mixed-models \
  -e api_keys.env \
  -n baseline_no_mixed
```

### 场景4: 更早使用GPT-4o-mini

```bash
# 在iter3就切换到GPT-4o-mini（而不是默认的iter5）
python run_batch_experiments.py \
  -g hard -l 10 \
  -i 5 -k 2 -m \
  --gpt-start-iter 3 \
  -e api_keys.env \
  -n early_gpt_test
```

### 场景5: 同时测试简单组和困难组

```bash
python run_batch_experiments.py \
  -g all \
  -i 5 -k 2 -m \
  -e api_keys.env \
  -n both_groups_test
```

### 场景6: 断点续传

```bash
# 第一次运行（假设中途中断了）
python run_batch_experiments.py -g hard -l 50 -i 5 -k 3 -m -e api_keys.env -n large_test

# 第二次运行（自动跳过已完成的题目）
python run_batch_experiments.py -g hard -l 50 -i 5 -k 3 -m -e api_keys.env -n large_test
```

### 场景7: 强制重新开始

```bash
python run_batch_experiments.py \
  -g hard -l 50 \
  -i 5 -k 3 -m \
  -e api_keys.env \
  -n fresh_start \
  --overwrite
```

---

## 🔧 参数详解

### 必需参数

无（所有参数都有默认值）

### 推荐参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--group` | `-g` | easy/hard/all | hard | 测试组别 |
| `--env-file` | `-e` | 文件路径 | None | **强烈建议指定** |
| `--experiment-name` | `-n` | 字符串 | None | **强烈建议指定** |

### 实验控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--limit` | `-l` | 整数 | None | 限制题目数，用于小规模测试 |
| `--iterations` | `-i` | 整数 | 配置文件值 | 最大迭代索引（实际执行N+1次） |
| `--candidates` | `-k` | 整数 | 配置文件值 | 每个迭代的候选数 |

### 混合模型参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--mixed-models` | 开关 | 配置文件值 | 启用混合模型 |
| `--no-mixed-models` | 开关 | False | 禁用混合模型 |
| `--gpt-start-iter` | 整数 | 5 | GPT-4o-mini开始的迭代号 |

### 输出控制参数

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--output-dir` | `-o` | 路径 | outputs/batch_tests | 输出目录基础路径 |
| `--overwrite` | - | 开关 | False | 覆盖已有输出 |

### 调试参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--verbose` | `-v` | 显示完整配置 |
| `--dry-run` | - | 仅显示配置，不运行 |

---

## 📊 输出结构说明

### 目录命名规则

```
outputs/batch_tests/{experiment_name}_{group}_{YYYYMMDD_HHMMSS}/
```

**示例**:
- `my_test_hard_20260414_084537/`
- `full_exp_all_20260414_090000/`

### 单个实验的内容

```
my_test_hard_20260414_084537/
├── Prob050_kmap1/           # 每个题目一个目录
│   ├── iter0/
│   │   ├── response0/       # 第1个候选
│   │   └── response1/       # 第2个候选
│   ├── iter1/
│   │   ├── response0/
│   │   └── response1/
│   ├── ...
│   └── log.txt              # 该题目的完整日志
├── Prob051_gates4/
├── ...
└── results_hard.json        # ⭐ 统计结果（重要！）
```

### 结果JSON文件内容

```json
{
  "timestamp": "2026-04-14T08:45:37.123456",
  "group": "hard",
  "config": {
    "iterations": 5,
    "candidates": 2,
    "mixed_models": true
  },
  "statistics": {
    "total": 3,
    "passed": 2,
    "failed": 1,
    "skipped": 0,
    "errors": 0,
    "pass_rate": 66.67,
    "elapsed_seconds": 40.8
  },
  "details": [
    {"problem": "Prob050_kmap1", "rank": 1.0},
    {"problem": "Prob051_gates4", "rank": 1.0},
    {"problem": "Prob052_gates100", "rank": 0.0}
  ]
}
```

---

## 🔍 监控和调试技巧

### 实时监控进度

```bash
# 方法1: 查看已完成题目数
watch -n 5 'ls outputs/batch_tests/exp_name_*/ | wc -l'

# 方法2: 查看实时日志
tail -f exp_name_*.log

# 方法3: 自定义监控脚本
while true; do
  completed=$(ls outputs/batch_tests/exp_name_*/ 2>/dev/null | wc -l)
  echo "Completed: $completed / 50"
  sleep 10
done
```

### 检查结果

```bash
# 查看所有实验的通过率
for dir in outputs/batch_tests/*/; do
  if [ -f "$dir/results_hard.json" ]; then
    name=$(basename "$dir")
    rate=$(jq '.statistics.pass_rate' "$dir/results_hard.json")
    time=$(jq '.statistics.elapsed_seconds' "$dir/results_hard.json")
    echo "$name: ${rate}% (${time}s)"
  fi
done

# 查看特定实验的详细信息
jq '.' outputs/batch_tests/my_test_*/results_hard.json

# 提取所有题目的Rank
jq '.details[] | "\(.problem): \(.rank)"' outputs/batch_tests/my_test_*/results_hard.json
```

### 调试配置

```bash
# Dry-run模式：只显示配置，不运行
python run_batch_experiments.py \
  -g hard -l 3 -i 5 -k 2 -m \
  -e api_keys.env \
  --dry-run --verbose

# 检查环境变量是否加载成功
python -c "import os; print('OPENAI_API_KEY:', 'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET')"
```

---

## ⚠️ 常见问题排查

### Q1: 提示缺少环境变量

```
❌ 缺少必需的环境变量: OPENAI_API_KEY
```

**解决**:
```bash
# 检查配置文件
cat api_keys.env

# 确保文件格式正确（每行 KEY=VALUE）
# 重新运行并指定配置文件
python run_batch_experiments.py -e api_keys.env ...
```

### Q2: 输出目录已存在

```
Info: Found existing output directory, resuming (completed 3 problems)
```

**这是正常行为**（断点续传）。如果想重新开始：
```bash
python run_batch_experiments.py ... --overwrite
```

### Q3: 测试卡住不动

**可能原因**:
1. API响应慢
2. 网络问题
3. 某道题特别复杂

**解决**:
```bash
# 查看当前正在处理的题目
tail -20 exp_name.log

# 如果长时间无响应，Ctrl+C停止后重新运行（会断点续传）
python run_batch_experiments.py ...  # 相同命令
```

### Q4: 如何清理旧数据

```bash
# 删除特定实验
rm -rf outputs/batch_tests/my_test_*

# 删除所有实验（谨慎！）
rm -rf outputs/batch_tests/*

# 只保留最近3个实验
ls -t outputs/batch_tests/ | tail -n +4 | xargs rm -rf
```

---

## 📖 更多资源

- **详细使用指南**: `BATCH_EXPERIMENTS_GUIDE.md` (11KB)
- **实施总结报告**: `PARAMETERIZED_BATCH_TEST_SUMMARY.md`
- **快速参考卡片**: `QUICK_REFERENCE.md`
- **帮助命令**: `python run_batch_experiments.py --help`

---

## 🎓 最佳实践

### 1. 始终先小规模验证

```bash
# ❌ 不要直接运行全量
python run_batch_experiments.py -g hard -i 5 -k 3 -m -e api_keys.env -n full

# ✅ 先小规模验证
python run_batch_experiments.py -g hard -l 3 -i 5 -k 3 -m -e api_keys.env -n test
# 确认无误后再全量
python run_batch_experiments.py -g hard -i 5 -k 3 -m -e api_keys.env -n full
```

### 2. 使用有意义的实验名称

```bash
# ❌ 不好的命名
-n test1
-n exp

# ✅ 好的命名
-n baseline_k1_iter5
-n mixed_k3_iter5_gpt3
-ablation_no_mixed_models
```

### 3. 记录实验配置

```bash
# 保存每次运行的命令到文件
echo "python run_batch_experiments.py -g hard -l 10 -i 5 -k 3 -m -e api_keys.env -n exp_001" >> experiment_log.txt
```

### 4. 定期备份结果

```bash
# 备份重要的实验结果
cp outputs/batch_tests/important_exp_*/results_*.json backups/
```

### 5. 后台运行时做好监控

```bash
# 启动后台任务
nohup python run_batch_experiments.py ... > log.txt 2>&1 &

# 设置提醒（完成后发送邮件或消息）
PID=$!
wait $PID && echo "Test completed!" | mail -s "AutoChip Test Done" your@email.com
```

---

## 🆚 新旧入口对比

| 特性 | 旧版 (batch_test.py) | 新版 (run_batch_experiments.py) |
|------|---------------------|--------------------------------|
| **配置方式** | 修改Python代码 | 命令行参数 |
| **环境变量** | 手动export | 配置文件管理 |
| **输出目录** | 固定路径，会覆盖 | 时间戳命名，不覆盖 |
| **断点续传** | 基于目录存在 | 基于Rank标记（更可靠） |
| **实验对比** | 手动整理 | 自动保存JSON |
| **学习曲线** | 需读代码 | 看文档即可 |
| **推荐使用** | 维护旧代码 | **所有新实验** ⭐ |

---

## 🎉 总结

**新版批量测试入口的核心优势**:

1. ✅ **零代码修改** - 所有配置通过命令行
2. ✅ **环境管理简化** - 配置文件统一管理API Keys
3. ✅ **数据安全** - 时间戳命名避免覆盖
4. ✅ **断点续传可靠** - 基于Rank标记精确判断
5. ✅ **易于对比** - JSON结果便于自动化分析

**立即开始使用**:

```bash
cd /home/gq/Autochip_workspace/AutoChip/autochip_scripts
source ~/miniconda3/etc/profile.d/conda.sh
conda activate autochip

# 第一步：小规模验证
python run_batch_experiments.py -g hard -l 3 -i 5 -k 2 -m -e api_keys.env -n my_test

# 第二步：查看结果
jq '.statistics' outputs/batch_tests/my_test_*/results_hard.json

# 第三步：全量测试
nohup python run_batch_experiments.py -g hard -i 5 -k 3 -m -e api_keys.env -n full_test > full.log 2>&1 &
```

---

**文档版本**: 1.0  
**最后更新**: 2026-04-14  
**维护者**: AutoChip Team
