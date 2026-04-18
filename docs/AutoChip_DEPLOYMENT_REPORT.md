# AutoChip 项目部署与微型示例运行报告

## 📋 执行摘要

本报告记录了 AutoChip 项目在本地环境的完整部署过程，包括环境配置、依赖安装、代码适配以及使用 Siliconflow API 成功运行 rule90 测试用例的全过程。

**核心成果：**
- ✅ 成功配置 Miniconda 环境（Python 3.10）
- ✅ 安装 Icarus Verilog 编译器（v10.3）
- ✅ 适配 Siliconflow API（Qwen/Qwen2.5-Coder-32B-Instruct）
- ✅ 成功生成 Rule 90 细胞自动机模块（首次迭代即通过，Rank 1.0）
- ✅ 总生成时间：5.26 秒

---

## 🔧 环境配置

### 1. 系统依赖安装

```bash
# 安装 Icarus Verilog 编译器
sudo apt-get update
sudo apt-get install -y iverilog

# 验证安装
iverilog -v
# 输出：Icarus Verilog version 10.3 (stable) (...)
```

### 2. Conda 环境创建

```bash
# 创建 Python 3.10 环境
conda create -n autochip python=3.10 -y

# 激活环境
conda activate autochip
```

### 3. 网络问题诊断与解决

**问题：** 系统配置了代理 `http://127.0.0.1:7890`，导致 pip 从清华源下载时出现 SSL 握手超时错误。

**解决方案：** 临时取消代理设置
```bash
unset http_proxy https_proxy all_proxy
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. Python 依赖包安装

修改后的 `requirements.txt`（移除重型本地模型依赖）：
```
openai
anthropic
google-generativeai
tiktoken
mistralai
```

安装命令：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**已安装包版本：**
- openai: 2.31.0
- anthropic: 0.92.0
- google-generativeai: 0.8.6
- tiktoken: 0.12.0
- mistralai: 2.3.1

---

## 💻 代码适配

### 1. languagemodels.py 修改

#### 修改点 1：ChatGPT 类支持自定义 base_url

```python
class ChatGPT(AbstractLLM):
    def __init__(self, model_id="gpt-3.5-turbo-16k", base_url=None):
        super().__init__()
        api_key = os.environ.get('OPENAI_API_KEY', '')
        self.model_id = model_id
        
        # Support for custom base_url (e.g., Siliconflow)
        if base_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)
```

#### 修改点 2：延迟导入重型依赖

**问题：** transformers 和 mistralai 的顶层导入导致即使不使用本地模型也会报错。

**解决方案：** 将导入移至类内部

```python
# 移除顶层导入
# from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
# from mistralai import Mistral

# 在 CodeLlama 类内添加
class CodeLlama(AbstractLLM):
    def __init__(self, model_id="codellama/CodeLlama-13b-hf"):
        super().__init__()
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers.models.llama import LlamaForCausalLM
        from transformers.models.code_llama.tokenization_code_llama import CodeLlamaTokenizer
        import torch
        # ... 其余代码

# 在 Mistral 类内添加
class Mistral(AbstractLLM):
    def __init__(self, model_id="open-mixtral-8x22b"):
        super().__init__()
        from mistralai import Mistral as MistralClient
        from mistralai.models import ChatMessage
        self.client = MistralClient(api_key=os.environ['MISTRAL_API_KEY'])
        self.ChatMessage = ChatMessage
```

### 2. verilog_handling.py 修改

添加 Siliconflow 模型支持：

```python
def generate_verilog_responses(conv, model_type, model_id="", num_candidates=1):
    match model_type:
        case "ChatGPT":
            model = lm.ChatGPT(model_id)
        case "Siliconflow":
            # Siliconflow is compatible with OpenAI API
            api_key = os.environ.get('OPENAI_API_KEY', '')
            base_url = os.environ.get('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')
            model = lm.ChatGPT(model_id, base_url=base_url)
        case "Claude":
            model = lm.Claude(model_id)
        # ... 其他模型
```

### 3. 配置文件创建

创建 `config_siliconflow.json`：

```json
{
    "general": {
        "prompt": "../verilogeval_prompts_tbs/validation_set/rule90/rule90.sv",
        "name": "top_module",
        "testbench": "../verilogeval_prompts_tbs/validation_set/rule90/rule90_tb.sv",
        "model_family": "Siliconflow",
        "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "num_candidates": 1,
        "iterations": 3,
        "outdir": "demo_output",
        "log": "log.txt",
        "mixed-models": false
    }
}
```

---

## 🚀 运行示例

### 1. 测试用例说明

**Rule 90 细胞自动机：**
- 一维 512-cell 系统
- 每个细胞的下一状态是其左右邻居的 XOR
- 边界条件：q[-1] = q[512] = 0

**设计描述文件：** `verilogeval_prompts_tbs/validation_set/rule90/rule90.sv`
**测试平台文件：** `verilogeval_prompts_tbs/validation_set/rule90/rule90_tb.sv`

### 2. 执行命令

```bash
cd /home/gq/Autochip_workspace/AutoChip/autochip_scripts
conda activate autochip
export OPENAI_API_KEY="sk-your-api-key-here"
unset http_proxy https_proxy all_proxy
python generate_verilog.py -c config_siliconflow.json
```

### 3. 运行结果

**控制台输出：**
```
Iteration: 0
Model type: Siliconflow
Model ID: Qwen/Qwen2.5-Coder-32B-Instruct
Number of responses: 1
Testbench ran successfully
Mismatches: 0
Samples: 7121
Input tokens: 0
Output tokens: 0
Cost for response 0: $0.0000000000
Response ranks: [1.0]
Response lengths: [350]
```

**关键指标：**
- ✅ **迭代次数：** 0（首次尝试即成功）
- ✅ **仿真匹配率：** 7121/7121 = 100%
- ✅ **代码评级：** Rank 1.0（完美通过）
- ⏱️ **生成时间：** 5.26 秒
- 💰 **API 成本：** $0.00（Siliconflow 当前免费或计费未适配）

### 4. 生成的 Verilog 代码

**文件位置：** `demo_output/iter0/response0/top_module.sv`

```verilog
module top_module(
    input clk,
    input load,
    input [511:0] data,
    output reg [511:0] q);

always @(posedge clk) begin
    if (load) begin
        q <= data;
    end else begin
        q[0] <= q[1]; // q[-1] is considered 0
        q[511] <= q[510]; // q[512] is considered 0
        for (int i = 1; i < 511; i = i + 1) begin
            q[i] <= q[i-1] ^ q[i+1];
        end
    end
end

endmodule
```

**代码分析：**
- ✅ 正确处理 load 信号（同步加载初始状态）
- ✅ 边界条件处理正确（q[0] 和 q[511] 特殊处理）
- ✅ 使用 for 循环实现中间细胞的 XOR 逻辑
- ✅ 使用非阻塞赋值（<=）符合同步时序逻辑规范

---

## 📊 输出文件结构

```
demo_output/
├── log.txt                          # 主日志文件（包含完整对话历史）
└── iter0/                           # 第 0 次迭代
    └── response0/                   # 第 0 个候选响应
        ├── log.txt                  # 响应详细日志
        ├── top_module.sv            # 生成的 Verilog 代码
        └── top_module.vvp           # 编译后的仿真可执行文件
```

---

## 🔍 技术洞察

### 1. Siliconflow API 兼容性

Siliconflow 完全兼容 OpenAI API 格式，只需：
- 设置 `OPENAI_API_KEY` 环境变量
- 指定 `base_url = "https://api.siliconflow.cn/v1"`
- 使用支持的模型 ID（如 `Qwen/Qwen2.5-Coder-32B-Instruct`）

### 2. AutoChip 迭代机制

对于简单用例（如 Rule 90），LLM 可能在首次迭代就生成正确代码。复杂设计可能需要多次迭代修复。

**迭代流程：**
1. LLM 生成 Verilog 代码
2. 正则表达式提取代码块
3. Icarus Verilog 编译检查
4. VVP 仿真验证
5. 解析 mismatches 数量
6. 若失败，将错误日志注入下一轮对话

### 3. Token 计费问题

当前显示 Input/Output tokens 均为 0，可能原因：
- Siliconflow API 响应格式与 OpenAI 略有差异
- `languagemodels.py` 中的 token 计数逻辑未适配 Siliconflow
- Siliconflow 当前提供免费额度

---

## ⚠️ 已知问题与改进建议

### 1. Google Generative AI 弃用警告

```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package.
```

**建议：** 如需使用 Gemini 模型，升级到新的 `google-genai` 包。

### 2. Token 计费适配

建议在 `LLMResponse` 类中添加对 Siliconflow 响应的 token 解析支持。

### 3. 错误处理增强

当前对 API 错误的处理较简单，建议添加：
- 重试机制（指数退避）
- 更详细的错误日志
- API 速率限制处理

---

## 📝 总结

本次部署成功验证了 AutoChip 框架的核心功能：

1. **环境配置：** 通过 Miniconda 实现了干净的依赖隔离
2. **API 适配：** Siliconflow 作为低成本替代方案完全可行
3. **代码生成：** Qwen2.5-Coder-32B 在简单用例上表现优异
4. **自动化闭环：** 编译-仿真-反馈机制工作正常

**下一步建议：**
- 测试更复杂的 HDLBits 题目（如 FSM、ALU 等）
- 验证多轮迭代修复机制
- 对比不同模型（GPT-4o-mini vs Qwen-32B）的性能差异
- 优化 Token 计费逻辑

---

**报告生成时间：** 2026-04-09  
**执行者：** AutoChip 部署助手  
**环境：** Ubuntu 20.04, Python 3.10, Icarus Verilog 10.3
