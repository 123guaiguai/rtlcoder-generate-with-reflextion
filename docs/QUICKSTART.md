# AutoChip 项目 - 快速开始指南

## 🎯 概述

AutoChip 是一个自动化的 Verilog 代码生成框架，通过 LLM + EDA 工具反馈实现代码的自主修复和优化。本项目已成功配置并可使用 Siliconflow API 或 GitHub Models 运行。

---

## ⚡ 快速开始（3 步运行）

### 方法 1：使用快速启动脚本（推荐）

```bash
cd /home/gq/Autochip_workspace/AutoChip

# 运行 rule90 测试用例（使用 Siliconflow）
./run_demo.sh rule90 siliconflow

# 或使用 GitHub Models
./run_demo.sh rule90 github
```

### 方法 2：手动运行

```bash
# 1. 激活环境
conda activate autochip

# 2. 设置 API Key
export OPENAI_API_KEY="sk-your-api-key-here"

# 3. 取消代理（避免网络问题）
unset http_proxy https_proxy all_proxy

# 4. 进入脚本目录
cd /home/gq/Autochip_workspace/AutoChip/autochip_scripts

# 5. 运行示例
python generate_verilog.py -c config_siliconflow.json
```

---

## 📁 项目结构

```
AutoChip/
├── autochip_scripts/              # 核心脚本目录
│   ├── generate_verilog.py        # 主入口文件
│   ├── verilog_handling.py        # 核心逻辑引擎
│   ├── languagemodels.py          # LLM 接口封装
│   ├── config_handler.py          # 配置解析
│   ├── config_siliconflow.json    # Siliconflow 配置
│   ├── config_github.json         # GitHub Models 配置
│   └── demo_output/               # 示例输出
├── verilogeval_prompts_tbs/       # 测试用例库
│   └── validation_set/
│       ├── rule90/                # Rule 90 细胞自动机
│       ├── rule110/               # Rule 110 细胞自动机
│       └── ...                    # 其他 HDLBits 题目
├── run_demo.sh                    # 快速启动脚本
├── requirements.txt               # Python 依赖
└── AutoChip_DEPLOYMENT_REPORT.md  # 详细部署报告
```

---

## 🔑 API 配置

### 可用的 API 池

项目中已配置以下 API（可在 `run_demo.sh` 中修改）：

| 提供商 | 模型 | API Key | Base URL |
|--------|------|---------|----------|
| **Siliconflow** | Qwen/Qwen2.5-Coder-32B-Instruct | `sk-your-api-key-here` | `https://api.siliconflow.cn/v1` |
| **GitHub Models** | gpt-4o-mini | `ghp-your-github-token-here` | `https://models.inference.ai.azure.com` |
| **Siliconflow** | Pro/zai-org/GLM-4.7 | `sk-hmbiuybbhzjqhhxefzxureuvymjkciixoaifvcbvaeqouqfq` | `https://api.siliconflow.cn/v1` |

### 切换 API

编辑 `run_demo.sh` 中的 `OPENAI_API_KEY` 和配置文件中的 `base_url` 即可切换。

---

## 🧪 测试用例

### 当前可用测试

| 测试名称 | 描述 | 难度 | 文件位置 |
|----------|------|------|----------|
| `rule90` | 512-cell 一维细胞自动机（Rule 90） | ⭐ | `validation_set/rule90/` |
| `rule110` | 512-cell 一维细胞自动机（Rule 110） | ⭐ | `validation_set/rule110/` |

### 运行不同测试

```bash
# 运行 rule110
./run_demo.sh rule110 siliconflow

# 运行其他测试（如果存在）
./run_demo.sh <test_name> siliconflow
```

---

## 📊 输出说明

每次运行会生成时间戳命名的输出目录：

```
output_rule90_20260409_163554/
├── log.txt                      # 完整对话日志
└── iter0/                       # 第 0 次迭代
    └── response0/               # 第 0 个候选
        ├── log.txt              # 响应详情
        ├── top_module.sv        # ✅ 生成的 Verilog 代码
        └── top_module.vvp       # 编译后的仿真文件
```

### 关键指标解读

- **Iteration:** 迭代次数（0 表示首次成功）
- **Mismatches:** 仿真不匹配数（0 表示完美通过）
- **Samples:** 总测试样本数
- **Rank:** 代码评级（1.0 = 完美，-1 = 编译失败）
- **Time to Generate:** 总生成时间（秒）

---

## 🛠️ 环境要求

### 系统依赖

- **Icarus Verilog:** v10.3+ （已安装）
- **Python:** 3.10 （通过 conda 管理）
- **操作系统:** Linux (Ubuntu 20.04+)

### Conda 环境

环境名：`autochip`

已安装的 Python 包：
- openai (2.31.0)
- anthropic (0.92.0)
- google-generativeai (0.8.6)
- tiktoken (0.12.0)
- mistralai (2.3.1)

---

## 🔧 故障排除

### 1. 网络代理问题

**症状：** pip 安装时出现 SSL 握手超时

**解决：**
```bash
unset http_proxy https_proxy all_proxy
```

### 2. Conda 环境不存在

**症状：** `conda activate autochip` 失败

**解决：**
```bash
conda create -n autochip python=3.10 -y
conda activate autochip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. Icarus Verilog 未安装

**症状：** `iverilog: command not found`

**解决：**
```bash
sudo apt-get update
sudo apt-get install -y iverilog
```

### 4. API Key 无效

**症状：** OpenAI API 返回 401 错误

**解决：** 检查 `OPENAI_API_KEY` 环境变量是否正确设置

---

## 📚 学习资源

- **详细部署报告：** [AutoChip_DEPLOYMENT_REPORT.md](AutoChip_DEPLOYMENT_REPORT.md)
- **项目架构分析：** [project_architecture_report.md](project_architecture_report.md)
- **原始论文：** `/papers/paper1.mmd`

---

## 🎓 下一步学习建议

1. **深入理解核心代码：**
   - 阅读 `verilog_handling.py` 中的 `verilog_loop()` 函数
   - 研究 `languagemodels.py` 中的 `calculate_rank()` 评估逻辑

2. **测试更复杂用例：**
   - 尝试 FSM（有限状态机）设计
   - 测试 ALU（算术逻辑单元）生成

3. **对比不同模型：**
   - 比较 Qwen-32B vs GPT-4o-mini 的性能
   - 分析多轮迭代的修复效果

4. **扩展功能：**
   - 添加新的 LLM 支持（如 Claude、Gemini）
   - 优化 Token 计费逻辑
   - 改进错误日志解析

---

## 📞 技术支持

如遇问题，请检查：
1. Conda 环境是否正确激活
2. API Key 是否有效
3. 网络连接是否正常（特别是代理设置）
4. 查看详细日志：`cat output_*/log.txt`

---

**最后更新：** 2026-04-09  
**维护者：** AutoChip 部署助手
