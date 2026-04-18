# AutoChip 参数化批量测试工具使用指南

## 📋 概述

`run_batch_experiments.py` 是一个全新的参数化批量测试工具，解决了旧版 `batch_test.py` 的以下问题：

1. **硬编码配置** - 所有实验参数可通过命令行控制，无需修改代码
2. **环境变量管理** - 支持配置文件管理API Keys，避免每次手动输入
3. **输出目录冲突** - 自动生成带时间戳的目录，支持断点续传而非覆盖
4. **灵活的实验范围** - 可选择测试简单组、困难组或全部

---

## 🚀 快速开始

### 1. 准备环境变量配置文件

创建 `api_keys.env` 文件（已提供示例 `api_keys.env.example`）：

```bash
# Siliconflow API Key (用于 Qwen 等模型)
OPENAI_API_KEY="sk-your-key-here"

# GitHub Models API Key (用于 GPT-4o-mini)
GPT4O_MINI_API_KEY="ghp-your-token-here"

# 是否启用相应模型
USE_SILICONFLOW=true
USE_GITHUB_MODELS=true
```

### 2. 运行小规模测试（验证配置）

```bash
cd /home/gq/Autochip_workspace/AutoChip/autochip_scripts
source ~/miniconda3/etc/profile.d/conda.sh
conda activate autochip

# 测试困难组前3题
python run_batch_experiments.py \
  --group hard \
  --limit 3 \
  --iterations 5 \
  --candidates 2 \
  --mixed-models \
  --gpt-start-iter 5 \
  --env-file api_keys.env \
  --experiment-name my_test
```

### 3. 运行全量测试

```bash
# 测试整个困难组
python run_batch_experiments.py \
  --group hard \
  --iterations 5 \
  --candidates 3 \
  --mixed-models \
  --gpt-start-iter 5 \
  --env-file api_keys.env \
  --experiment-name full_hard_test
```

---

## 📖 命令行参数详解

### 实验范围控制

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--group` | `-g` | 测试组别: easy/hard/all | `--group hard` |
| `--limit` | `-l` | 限制题目数量（小规模测试） | `--limit 3` |

### 实验参数控制

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--iterations` | `-i` | 最大迭代次数（实际执行 iterations+1 次） | 使用配置文件 |
| `--candidates` | `-k` | 每个迭代的候选数量 | 使用配置文件 |
| `--mixed-models` | `-m` | 启用混合模型策略 | 使用配置文件 |
| `--no-mixed-models` | - | 禁用混合模型策略 | - |
| `--gpt-start-iter` | - | GPT-4o-mini 开始的迭代序号 | 5 |

### 输出控制

| 参数 | 简写 | 说明 |
|------|------|------|
| `--output-dir` | `-o` | 输出目录基础路径 | `outputs/batch_tests` |
| `--experiment-name` | `-n` | 实验名称（生成带时间戳的目录） |
| `--overwrite` | - | 如果目录存在则覆盖（默认断点续传） |

### 环境配置

| 参数 | 简写 | 说明 |
|------|------|------|
| `--env-file` | `-e` | 环境变量配置文件路径 |
| `--api-key` | - | 直接设置API Key（可多次使用） |

### 其他选项

| 参数 | 简写 | 说明 |
|------|------|------|
| `--verbose` | `-v` | 显示详细配置信息 |
| `--dry-run` | - | 仅显示配置，不实际运行 |

---

## 💡 使用示例

### 示例 1: 小规模验证新配置

```bash
# 测试困难组前3题，2次迭代，2个候选，不使用混合模型
python run_batch_experiments.py \
  -g hard -l 3 -i 2 -k 2 \
  --no-mixed-models \
  -e api_keys.env \
  -n quick_test
```

### 示例 2: 对比不同迭代次数的效果

```bash
# 实验1: 3次迭代
python run_batch_experiments.py -g hard -l 10 -i 3 -k 2 -m -n iter3_test -e api_keys.env

# 实验2: 6次迭代
python run_batch_experiments.py -g hard -l 10 -i 6 -k 2 -m -n iter6_test -e api_keys.env
```

### 示例 3: 同时测试两组

```bash
python run_batch_experiments.py \
  -g all \
  -i 5 -k 3 -m \
  -e api_keys.env \
  -n full_comparison
```

### 示例 4: 直接在命令行设置API Key

```bash
python run_batch_experiments.py \
  -g hard -l 3 \
  --api-key OPENAI_API_KEY sk-xxx \
  --api-key GPT4O_MINI_API_KEY ghp_xxx \
  -n cmdline_test
```

### 示例 5: Dry-run 模式（检查配置）

```bash
python run_batch_experiments.py \
  -g hard -l 3 -i 5 -k 2 -m \
  -e api_keys.env \
  --dry-run --verbose
```

---

## 📁 输出目录结构

### 目录命名规则

每次运行都会生成带时间戳的新目录，不会覆盖旧数据：

```
outputs/batch_tests/
├── test_param_hard_20260414_084302/    # 第一次运行
├── test_param_hard_20260414_085123/    # 第二次运行
└── full_hard_test_hard_20260414_090000/ # 全量测试
```

### 单个实验的输出

```
outputs/batch_tests/{experiment_name}_{group}_{timestamp}/
├── Prob050_kmap1/
│   ├── iter0/
│   │   ├── response0/
│   │   └── response1/
│   ├── iter1/
│   │   ├── response0/
│   │   └── response1/
│   ├── ...
│   └── log.txt
├── Prob051_gates4/
├── ...
└── results_{group}.json  # 统计结果
```

---

## 🔄 断点续传机制

### 工作原理

1. **检测已有输出** - 如果输出目录已存在，自动检测已完成的题目
2. **跳过已完成题目** - 读取 `log.txt`，如果包含 "Rank of best response:" 则跳过
3. **继续未完成题目** - 只运行未完成的题目

### 使用场景

- **网络中断** - 重新运行相同命令，自动从断点继续
- **手动停止** - Ctrl+C 停止后，重新运行即可继续
- **增量测试** - 添加新题目后，重新运行只测试新增部分

### 强制覆盖

如果需要重新开始（不保留旧数据），使用 `--overwrite` 参数：

```bash
python run_batch_experiments.py \
  -g hard -l 3 \
  --overwrite \
  -e api_keys.env \
  -n fresh_test
```

---

## 📊 结果分析

### JSON 结果文件

每个实验生成 `results_{group}.json`，包含：

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

### 快速查看结果

```bash
# 查看通过率
cat outputs/batch_tests/*/results_hard.json | jq '.statistics.pass_rate'

# 查看所有实验的对比
for f in outputs/batch_tests/*/results_hard.json; do
  echo "$f: $(jq '.statistics.pass_rate' $f)%"
done
```

---

## 🔧 高级用法

### 1. 自定义混合模型策略

修改 `batch_test.py` 中的 `GROUP_CONFIGS`，然后通过命令行指定：

```bash
# 在 iter3 就切换到 GPT-4o-mini（更早使用强模型）
python run_batch_experiments.py \
  -g hard -l 5 \
  -i 5 -k 2 -m \
  --gpt-start-iter 3 \
  -e api_keys.env
```

### 2. 批量运行多个实验

创建脚本 `run_experiments.sh`：

```bash
#!/bin/bash

# 实验1: 基准测试（无混合模型）
python run_batch_experiments.py -g hard -l 10 -i 5 -k 2 --no-mixed-models -e api_keys.env -n baseline

# 实验2: 混合模型（iter5切换）
python run_batch_experiments.py -g hard -l 10 -i 5 -k 2 -m --gpt-start-iter 5 -e api_keys.env -n mixed_iter5

# 实验3: 混合模型（iter3切换）
python run_batch_experiments.py -g hard -l 10 -i 5 -k 2 -m --gpt-start-iter 3 -e api_keys.env -n mixed_iter3
```

### 3. 后台运行全量测试

```bash
nohup python run_batch_experiments.py \
  -g hard \
  -i 5 -k 3 -m \
  -e api_keys.env \
  -n full_test_$(date +%Y%m%d) \
  > full_test.log 2>&1 &

echo "PID: $!"
tail -f full_test.log
```

---

## ⚠️ 注意事项

### 1. 环境变量配置文件安全

- **不要将 `api_keys.env` 提交到 Git**
- 已在 `.gitignore` 中添加该文件
- 定期轮换 API Keys

### 2. 资源消耗估算

| 配置 | API调用次数 | 预估成本 |
|------|------------|---------|
| 10题, 5迭代, 2候选, 无混合 | 10×6×2 = 120 | ~$0.12 |
| 50题, 5迭代, 3候选, 混合 | 50×6×3 = 900 | ~$0.90 |
| 100题, 5迭代, 3候选, 混合 | 100×6×3 = 1800 | ~$1.80 |

*假设 Siliconflow 费用为 $0.001/次，GitHub Models 免费*

### 3. 迭代次数理解

- `--iterations 5` 表示执行 **6次迭代**（iter0-iter5）
- 这是因为 `max_iterations` 是最大索引值，不是次数
- 如果希望执行N次，设置 `--iterations N-1`

### 4. 断点续传的局限

- 只检查 `log.txt` 中是否有 Rank 信息
- 如果日志损坏或不完整，可能重复运行
- 使用 `--overwrite` 可以强制重新开始

---

## 🆚 与旧版 batch_test.py 对比

| 特性 | 旧版 (batch_test.py) | 新版 (run_batch_experiments.py) |
|------|---------------------|--------------------------------|
| 配置方式 | 修改代码 | 命令行参数 |
| 环境变量 | 手动 export | 配置文件管理 |
| 输出目录 | 固定路径，会覆盖 | 带时间戳，不覆盖 |
| 断点续传 | 基于目录存在性 | 基于Rank信息检测 |
| 实验对比 | 需手动管理 | 自动区分不同实验 |
| 灵活性 | 低 | 高 |

**建议**: 新功能开发和实验统一使用新版工具，旧版仅用于维护历史代码。

---

## 📞 常见问题

### Q1: 如何查看某个题目的详细输出？

```bash
ls outputs/batch_tests/{experiment_name}/Prob050_kmap1/
cat outputs/batch_tests/{experiment_name}/Prob050_kmap1/log.txt
```

### Q2: 如何中途停止并继续？

```bash
# 停止
Ctrl+C

# 继续（使用相同命令）
python run_batch_experiments.py -g hard -l 50 -i 5 -k 3 -m -e api_keys.env -n my_test
```

### Q3: 如何清理旧的测试输出？

```bash
# 删除特定实验
rm -rf outputs/batch_tests/test_param_*

# 删除所有测试
rm -rf outputs/batch_tests/*
```

### Q4: 如何对比不同实验的效果？

```bash
# 提取所有实验的通过率
for dir in outputs/batch_tests/*/; do
  if [ -f "$dir/results_hard.json" ]; then
    rate=$(jq '.statistics.pass_rate' "$dir/results_hard.json")
    name=$(basename "$dir")
    echo "$name: $rate%"
  fi
done
```

---

## 🎯 最佳实践

1. **小规模验证** - 任何新配置先用 `--limit 3` 测试
2. **命名规范** - 使用有意义的实验名称，如 `baseline_v1`, `mixed_iter3`
3. **记录配置** - 保存每次实验的命令行参数，便于复现
4. **定期检查** - 后台运行时定期检查日志，确保正常运行
5. **备份结果** - 重要实验的结果JSON文件单独备份

---

**最后更新**: 2026-04-14  
**版本**: 1.0  
**作者**: AutoChip Team
