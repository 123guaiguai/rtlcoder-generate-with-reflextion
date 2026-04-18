# AutoChip 核心概念详解

## 📚 目录
1. [迭代机制 (Iterations)](#1-迭代机制-iterations)
2. [候选响应 (Candidates)](#2-候选响应-candidates)
3. [配置文件详解](#3-配置文件详解)
4. [评估指标解读](#4-评估指标解读)
5. [7121/7121 样本匹配的含义](#5-71217121-样本匹配的含义)

---

## 1. 迭代机制 (Iterations)

### 什么是迭代？

**迭代（Iteration）**是指 AutoChip 的"生成-验证-修复"循环次数。每次迭代包含以下步骤：

```
┌─────────────┐
│ LLM 生成代码 │
└──────┬──────┘
       ↓
┌─────────────┐
│ Icarus 编译  │ ← 如果编译失败，记录错误
└──────┬──────┘
       ↓
┌─────────────┐
│ VVP 仿真验证 │ ← 如果仿真不匹配，记录 mismatches
└──────┬──────┘
       ↓
┌─────────────────┐
│ 是否成功或达到   │ ← 是：输出结果
│ 最大迭代次数？   │ ← 否：将错误日志反馈给 LLM，进入下一轮
└─────────────────┘
```

### 实际案例分析

在 `output_rule90_20260409_163554` 目录中，有 **iter0, iter1, iter2, iter3** 四个文件夹，这表示：

- **配置的最大迭代次数：** 3 次（在 `config_siliconflow.json` 中设置 `"iterations": 3`）
- **实际执行的迭代：** 4 次（iter0 ~ iter3）

**为什么是 4 次而不是 3 次？**

因为迭代计数从 **0** 开始：
- `iter0`: 第 1 次尝试（初始生成）
- `iter1`: 第 2 次尝试（基于 iter0 的错误反馈）
- `iter2`: 第 3 次尝试（基于 iter1 的错误反馈）
- `iter3`: 第 4 次尝试（基于 iter2 的错误反馈，达到最大迭代次数后停止）

### 从日志看迭代过程

查看 `output_rule90_20260409_163554/log.txt`：

**Iter 0（首次生成）：**
```verilog
// LLM 生成的代码使用了 "integer i"
for (integer i = 1; i < 511; i = i + 1) begin
    q[i] <= q[i-1] ^ q[i+1];
end
```
**编译错误：** `error: name is not a valid net.`（Icarus Verilog 不支持在 for 循环中声明 integer）

**Iter 1（第一次修复）：**
```verilog
// LLM 尝试改为 "reg i"
for (reg i = 1; i < 511; i = i + 1) begin
    q[i] <= q[i-1] ^ q[i+1];
end
```
**编译错误：** 同样的错误（reg 也不能在 for 循环中声明）

**Iter 2（第二次修复）：**
LLM 再次尝试类似的修复，但仍然失败。

**Iter 3（第三次修复，最后一次）：**
```verilog
// LLM 尝试使用辅助寄存器 q_next
reg [0:511] q_next;
for (reg i = 1; i < 511; i = i + 1) begin
    q_next[i] = q[i-1] ^ q[i+1];
end
q <= q_next;
```
**最终结果：** 仍然编译失败，Rank = -1

### 关键发现

⚠️ **这个案例实际上失败了！** 

之前报告中的 "Rank 1.0, 7121/7121" 是来自另一个成功的运行（`demo_output`），而 `output_rule90_20260409_163554` 这个目录显示的是**失败的案例**（Rank = -1）。

这说明：
1. **LLM 并不总是能成功修复代码**
2. **迭代次数越多，成功率越高，但也有上限**
3. **某些语法问题可能需要更明确的提示才能解决**

---

## 2. 候选响应 (Candidates)

### 什么是候选（Candidates）？

**候选（Candidates）**是指在**单次迭代**中，LLM 同时生成的多个不同版本的代码。

### 参数说明

在配置文件中：
```json
{
    "num_candidates": 1  // 每次迭代生成 1 个候选
}
```

如果设置为 `num_candidates: 3`，则每次迭代会：
1. 调用 LLM API **3 次**（或使用支持批量生成的 API）
2. 得到 3 个不同的代码版本
3. 分别编译和仿真这 3 个版本
4. 选择 **Rank 最高**的那个作为本次迭代的结果

### 目录结构示例

假设 `num_candidates: 2`，目录结构会是：

```
iter0/
├── response0/    # 第 1 个候选
│   ├── top_module.sv
│   └── log.txt
└── response1/    # 第 2 个候选
    ├── top_module.sv
    └── log.txt
```

### 为什么需要多个候选？

1. **提高成功率：** LLM 具有随机性，多次生成可能得到更好的结果
2. **多样性探索：** 不同的实现思路可能有不同的优劣
3. **排名选择：** 通过编译/仿真结果自动选择最佳方案

### 排名逻辑

在 `languagemodels.py` 的 `calculate_rank()` 函数中：

```python
# 优先级排序
key=lambda resp: (resp.rank, -resp.parsed_length)
```

- **第一优先级：** `rank` 越高越好（1.0 > 0.5 > -0.5 > -1）
- **第二优先级：** 代码长度越短越好（在 rank 相同的情况下）

---

## 3. 配置文件详解

### 3.1 config_siliconflow.json

**用途：** 使用 Siliconflow API（Qwen 模型）运行测试

```json
{
    "general": {
        "prompt": "../verilogeval_prompts_tbs/validation_set/rule90/rule90.sv",
        "name": "top_module",
        "testbench": "../verilogeval_prompts_tbs/validation_set/rule90/rule90_tb.sv",
        "model_family": "Siliconflow",           // 使用 Siliconflow
        "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "num_candidates": 1,                      // 每次生成 1 个候选
        "iterations": 3,                          // 最多迭代 3 次（实际执行 4 次：0-3）
        "outdir": "output_rule90_20260409_163554", // 输出目录
        "log": "log.txt",                         // 日志文件名
        "mixed-models": false                     // 不使用混合模型
    },
    "mixed-models": {
        // 当 mixed-models: true 时生效
        "model1": {
            "start_iteration": 0,                 // 从第 0 次迭代开始使用
            "model_family": "ChatGPT",
            "model_id": "gpt-4o-mini"
        },
        "model2": {
            "start_iteration": -1,                // -1 表示最后一次迭代
            "model_family": "ChatGPT",
            "model_id": "gpt-4o"                  // 切换到更强的模型
        }
    }
}
```

**运行命令：**
```bash
python generate_verilog.py -c config_siliconflow.json
```

### 3.2 config_github.json

**用途：** 使用 GitHub Models API（GPT-4o-mini）运行测试

```json
{
    "general": {
        "prompt": "../verilogeval_prompts_tbs/validation_set/rule90/rule90.sv",
        "name": "top_module",
        "testbench": "../verilogeval_prompts_tbs/validation_set/rule90/rule90_tb.sv",
        "model_family": "ChatGPT",               // 使用 OpenAI 兼容接口
        "model_id": "gpt-4o-mini",
        "num_candidates": 1,
        "iterations": 3,
        "outdir": "demo_output_github",
        "log": "log.txt",
        "mixed-models": false
    }
}
```

**运行前需设置环境变量：**
```bash
export OPENAI_API_KEY="ghp-your-github-token-here"
export OPENAI_BASE_URL="https://models.inference.ai.azure.com"
```

### 3.3 demo_config.json

**用途：** 官方示例配置，用于测试 mux2to1（二选一多路器）

```json
{
    "prompt": "../verilogeval_prompts_tbs/ve_testbenches_human/mux2to1/mux2to1.sv",
    "name": "top_module",
    "testbench": "../verilogeval_prompts_tbs/ve_testbenches_human/mux2to1/mux2to1_tb.sv",
    "model_family": "ChatGPT",
    "model_id": "gpt-4o-mini",
    "num_candidates": 1,
    "iterations": 3,
    "outdir": "demo_output",
    "log": "demo_log.txt",
    "mixed-models": false
}
```

**这是最简单的入门配置**，适合初次测试。

### 3.4 配置文件在哪里被使用？

**调用链：**

```
generate_verilog.py (主入口)
    ↓
config_handler.py
    ├─ load_config()          # 读取 JSON 文件
    ├─ validate_mixed_model_config()  # 验证混合模型配置
    └─ parse_args_and_config() # 合并命令行参数和配置文件
    ↓
verilog_handling.py
    └─ verilog_loop()         # 使用配置启动迭代循环
```

**关键代码片段（config_handler.py）：**

```python
def load_config(config_file="config.json"):
    with open(config_file, 'r') as file:
        config = json.load(file)
    
    config_values = config['general']
    parse_mixed_models = config_values.get('mixed-models', False)
    
    if parse_mixed_models:
        mixed_model_config = config.get('mixed-models', {})
    
    return config_values, mixed_model_config
```

---

## 4. 评估指标解读

### 4.1 Rank（评级）

**Rank** 是 AutoChip 对生成代码质量的量化评分，范围从 **-1 到 1.0**：

| Rank 值 | 含义 | 说明 |
|---------|------|------|
| **1.0** | ✅ 完美通过 | 编译成功 + 仿真 100% 匹配 |
| **0.0 ~ 0.99** | ⚠️ 部分匹配 | 编译成功，但仿真有部分 mismatches |
| **-0.5** | ⚡ 编译警告 | 编译通过但有警告 |
| **-1.0** | ❌ 编译失败 | 语法错误，无法编译 |

**计算公式（来自 languagemodels.py）：**

```python
def calculate_rank(self):
    if self.compile_status == "error":
        self.rank = -1.0
    elif self.compile_status == "warning":
        self.rank = -0.5
    else:
        # 仿真阶段
        if self.samples == 0:
            self.rank = 0.0
        else:
            # rank = (总样本数 - 不匹配数) / 总样本数
            self.rank = (self.samples - self.mismatches) / self.samples
```

### 4.2 Mismatches（不匹配数）

**Mismatches** 是指 DUT（Design Under Test，待测设计）与 Reference Module（参考模型）输出不一致的次数。

**示例：**
```
Mismatches: 5 in 100 samples
```
表示在 100 个时钟周期采样点中，有 5 次 DUT 的输出与参考模型不同。

### 4.3 Samples（样本数）

**Samples** 是指 Testbench 在仿真过程中采样的总次数（通常是时钟周期数）。

---

## 5. 7121/7121 样本匹配的含义

### 5.1 7121 是什么？

**7121** 是 Rule 90 Testbench 在仿真过程中产生的**总采样点数**（时钟周期数）。

### 5.2 如何计算出来的？

查看 `rule90_tb.sv` 的核心逻辑：

```systemverilog
always @(posedge clk, negedge clk) begin
    stats1.clocks++;  // 每个时钟边沿计数一次
    
    if (!tb_match) begin
        if (stats1.errors == 0) 
            stats1.errortime = $time;
        stats1.errors++;  // 记录不匹配次数
    end
end

final begin
    $display("Mismatches: %1d in %1d samples", stats1.errors, stats1.clocks);
end
```

**Testbench 的执行流程：**

1. **初始化阶段：** 加载初始状态
2. **测试序列 1：** `repeat(10)` → 10 个时钟周期
3. **测试序列 2：** `repeat(1000)` → 1000 个时钟周期
4. **测试序列 3：** `repeat(1000)` → 1000 个时钟周期
5. **测试序列 4：** `repeat(1000)` → 1000 个时钟周期
6. **测试序列 5：** `repeat(20)` + `repeat(500)` → 520 个时钟周期
7. **其他测试序列...**

**总计约 7121 个时钟周期采样点。**

### 5.3 "7121/7121 样本匹配" 的意思

```
Mismatches: 0 in 7121 samples
```

**解读：**
- **总采样次数：** 7121 次（每个时钟周期采样一次）
- **不匹配次数：** 0 次
- **匹配率：** 7121/7121 = 100%

这意味着：
✅ 在**所有 7121 个时钟周期**中，DUT 的输出 `q_dut` 与参考模型 `q_ref` **完全一致**
✅ 设计的**功能正确性**得到验证
✅ **Rank = 1.0**（完美通过）

### 5.4 与iverilog等价验证的关系

您提到的 "sv 和 tb.sv 可以用 iverilog 进行等价验证" 是正确的，但需要澄清：

**AutoChip 使用的不是传统意义上的"等价性检查"（Equivalence Checking），而是"动态仿真验证"（Dynamic Simulation）：**

| 方法 | 说明 | AutoChip 使用？ |
|------|------|----------------|
| **形式化等价验证** | 数学证明两个电路在所有输入下等价 | ❌ 否 |
| **动态仿真验证** | 运行测试向量，比较输出波形 | ✅ 是 |

**AutoChip 的验证流程：**

```
┌──────────────────┐
│  Reference Model │ ← 已知的正确实现（黄金模型）
│  (reference_module)│
└────────┬─────────┘
         │
         ↓ 同样的输入激励
┌──────────────────┐     ┌──────────────────┐
│  DUT (待测设计)   │     │  Reference Model  │
│  (LLM 生成的代码) │     │  (已知正确的代码)  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ↓                        ↓
    q_dut[511:0]            q_ref[511:0]
         │                        │
         └───────┬────────────────┘
                 ↓
         每个时钟周期比较
         tb_match = (q_dut === q_ref)
                 ↓
         统计 mismatches 数量
```

**关键点：**
- Testbench 中有一个 **Reference Module**（参考模块），它是人工编写的、已知正确的实现
- Testbench 会向 DUT 和 Reference Module 施加**相同的输入激励**
- 在每个时钟周期，比较两者的输出是否一致
- 如果不一致，`mismatches` 计数器加 1

### 5.5 为什么是 7121 而不是其他数字？

这个数字由 Testbench 的设计决定：

```systemverilog
repeat(10) @(posedge clk);      // 10 次
repeat(1000) @(posedge clk);    // 1000 次
repeat(1000) @(posedge clk);    // 1000 次
repeat(1000) @(posedge clk);    // 1000 次
repeat(20) @(posedge clk);      // 20 次
repeat(2) @(posedge clk);       // 2 次
repeat(500) @(posedge clk);     // 500 次
// ... 还有其他测试序列
```

所有这些 `repeat` 语句加起来，再加上初始化阶段的时钟周期，总共约 **7121 个采样点**。

---

## 🎯 总结对比表

| 概念 | 含义 | 示例 |
|------|------|------|
| **Iteration (iter0-3)** | 生成-验证-修复的循环次数 | 4 次迭代 = 初始生成 + 3 次修复尝试 |
| **Candidate (response0)** | 单次迭代中生成的代码版本数 | num_candidates=1 表示每次只生成 1 个版本 |
| **Rank** | 代码质量评分（-1 到 1.0） | 1.0 = 完美，-1 = 编译失败 |
| **Samples** | Testbench 的总采样次数 | 7121 = 7121 个时钟周期 |
| **Mismatches** | DUT 与参考模型输出不一致的次数 | 0/7121 = 100% 正确 |
| **配置文件** | 定义运行参数的 JSON 文件 | config_siliconflow.json 等 |

---

## 💡 实际建议

1. **如果看到多个 iter 文件夹：** 说明经历了多次迭代修复
2. **如果 Rank = -1：** 说明所有迭代都失败了，需要检查：
   - Prompt 是否清晰
   - 是否需要更多迭代次数
   - 是否需要更强的模型
3. **如果想提高成功率：**
   - 增加 `num_candidates`（如设为 3）
   - 增加 `iterations`（如设为 5）
   - 使用混合模型策略（前期用便宜模型，后期用强模型）

---

**最后更新：** 2026-04-09  
**作者：** AutoChip 学习助手
