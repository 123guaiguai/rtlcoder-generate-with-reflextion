# 🚀 AutoChip Workspace GitHub上传指南

## 📋 上传前准备清单

### 1️⃣ 初始化Git仓库（如果还没有）

```bash
cd /home/gq/Autochip_workspace

# 初始化Git仓库
git init

# 添加远程仓库（替换为你的GitHub仓库地址）
git remote add origin https://github.com/你的用户名/AutoChip-Workspace.git
```

### 2️⃣ 确认敏感文件被忽略

检查 `.gitignore` 是否正确配置：

```bash
# 查看哪些文件会被Git跟踪
git status

# 确认以下文件**不在**列表中：
# - AutoChip/.autochip_api_keys.py ❌ (不应出现)
# - AutoChip/autochip_scripts/outputs/ ❌ (不应出现)
# - *.log ❌ (不应出现)
```

### 3️⃣ 创建API密钥配置文件

```bash
cd /home/gq/Autochip_workspace/AutoChip

# 如果还没有配置文件，复制示例文件
if [ ! -f .autochip_api_keys.py ]; then
    cp .autochip_api_keys.example.py .autochip_api_keys.py
fi

# 编辑配置文件，填入真实密钥
vim .autochip_api_keys.py
```

配置文件内容示例：
```python
# Siliconflow API配置
SILICONFLOW_CONFIG = {
    'api_key': 'sk-your-real-key-here',  # ← 替换
    'base_url': 'https://api.siliconflow.cn/v1'
}

# GitHub Models API配置
GITHUB_CONFIG = {
    'api_key': 'ghp-your-real-token-here',  # ← 替换
    'base_url': 'https://models.inference.ai.azure.com'
}
```

### 4️⃣ 首次提交

```bash
cd /home/gq/Autochip_workspace

# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 检查即将提交的文件列表
git status

# 确认无误后提交
git commit -m "Initial commit: AutoChip workspace with secure API key management"

# 推送到GitHub
git push -u origin main
```

---

## 🔒 安全验证步骤

### 验证1：确认敏感文件未被跟踪

```bash
cd /home/gq/Autochip_workspace

# 方法1：检查git status
git status | grep ".autochip_api_keys.py"
# 应该没有输出 ✅

# 方法2：使用git check-ignore
git check-ignore AutoChip/.autochip_api_keys.py
# 应该输出：AutoChip/.autochip_api_keys.py ✅

# 方法3：列出所有被跟踪的文件
git ls-files | grep -E "api_key|\.env|outputs/"
# 应该没有输出 ✅
```

### 验证2：模拟推送测试

```bash
# 在本地查看所有将被推送的文件
git diff --cached --name-only

# 确认不包含敏感文件后，再执行真正的push
git push --dry-run origin main
```

---

## ⚠️ 常见错误及解决方案

### 错误1：不小心提交了敏感文件

**症状**：`.autochip_api_keys.py` 出现在 `git status` 中

**解决**：
```bash
# 1. 从暂存区移除
git rm --cached AutoChip/.autochip_api_keys.py

# 2. 提交更改
git commit -m "Remove sensitive API key file from tracking"

# 3. 确保.gitignore生效
echo "AutoChip/.autochip_api_keys.py" >> .gitignore
git add .gitignore
git commit -m "Add API key file to gitignore"
```

### 错误2：已经推送到GitHub的敏感文件

**紧急处理**：
```bash
# 1. 立即在API提供商处撤销密钥！

# 2. 生成新密钥并更新 .autochip_api_keys.py

# 3. 从Git历史中彻底删除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch AutoChip/.autochip_api_keys.py' \
  --prune-empty --tag-name-filter cat -- --all

# 4. 强制推送到GitHub（会覆盖远程历史）
git push origin --force --all

# 5. 通知所有协作者重新克隆仓库
```

### 错误3： outputs/ 目录太大

**解决**：
```bash
# 1. 清理大型输出文件
rm -rf AutoChip/autochip_scripts/outputs/*

# 2. 添加到.gitignore（已包含）
# AutoChip/autochip_scripts/outputs/

# 3. 如果已经被跟踪，移除它
git rm -r --cached AutoChip/autochip_scripts/outputs/
git commit -m "Remove large output files from tracking"
```

---

## 📊 推荐的项目结构

上传到GitHub后的项目结构应该是：

```
AutoChip-Workspace/
├── .gitignore                          # ✅ Git忽略规则
├── README.md                           # ✅ 项目说明
├── docs/                               # ✅ 文档
│   ├── 参数化批量测试快速参考.md
│   └── ...
├── AutoChip/
│   ├── .autochip_api_keys.example.py   # ✅ API密钥示例（公开）
│   ├── .autochip_api_keys.py           # ❌ 真实密钥（不上传）
│   ├── README.md                       # ✅ AutoChip说明
│   ├── API_KEYS_SECURITY_GUIDE.md      # ✅ 安全指南
│   ├── QUICK_START_SECURITY.md         # ✅ 快速参考
│   ├── autochip_scripts/               # ✅ 核心脚本
│   │   ├── languagemodels.py
│   │   ├── batch_test.py
│   │   ├── analyze_batch_results.py
│   │   ├── configs/                    # ✅ 配置模板
│   │   │   ├── config_Prob050_kmap1.json
│   │   │   └── ...
│   │   └── outputs/                    # ❌ 输出文件（不上传）
│   ├── VerilogEval/                    # ✅ 评估数据集
│   └── verilogeval_prompts_tbs/        # ✅ 提示词和测试平台
└── ...
```

---

## 🔄 团队协作最佳实践

### 为新成员提供设置说明

在项目的 `README.md` 中添加：

```markdown
## 🔐 首次使用配置

1. 克隆仓库：
   ```bash
   git clone https://github.com/你的用户名/AutoChip-Workspace.git
   cd AutoChip-Workspace/AutoChip
   ```

2. 配置API密钥：
   ```bash
   cp .autochip_api_keys.example.py .autochip_api_keys.py
   vim .autochip_api_keys.py  # 填入你的API密钥
   ```

3. 安装依赖并运行：
   ```bash
   conda activate autochip
   python autochip_scripts/run_batch_experiments.py -g hard -l 3 -i 2 -k 2 --mixed-models -n test
   ```
```

### 定期轮换密钥

建议每3-6个月更新一次API密钥：

```bash
# 1. 在API提供商控制台生成新密钥
# 2. 更新 .autochip_api_keys.py
vim AutoChip/.autochip_api_keys.py

# 3. 测试新密钥
conda run -n autochip python AutoChip/autochip_scripts/generate_verilog.py \
    -c AutoChip/autochip_scripts/configs/config_Prob050_kmap1.json \
    -o /tmp/test_new_key/Prob050

# 4. 旧密钥可以在确认新密钥工作后撤销
```

---

## 📝 提交规范

### Commit Message规范

```bash
# 功能更新
git commit -m "feat: add mixed model support for hard group"

# Bug修复
git commit -m "fix: correct rank calculation in check_if_completed"

# 文档更新
git commit -m "docs: update API key security guide"

# 配置更改（不包含密钥）
git commit -m "config: update default iterations to 5 for hard group"
```

### 分支策略

```bash
# 主分支：稳定版本
git checkout main

# 开发分支：新功能
git checkout -b feature/mixed-model-optimization

# 修复分支：Bug修复
git checkout -b fix/rank-calculation-bug
```

---

## 🆘 紧急联系

如果发现密钥泄露：

1. **立即行动**：
   - Siliconflow: https://cloud.siliconflow.cn/account/apikeys
   - GitHub: https://github.com/settings/tokens

2. **撤销密钥**：在对应平台立即撤销泄露的密钥

3. **生成新密钥**：创建新的API密钥并更新配置

4. **清理历史**：按照上述"错误2"的步骤清理Git历史

5. **通知团队**：告知所有协作者更新他们的配置

---

## ✅ 最终检查清单

在点击"Push to GitHub"之前：

- [ ] `.gitignore` 已创建并包含所有敏感文件模式
- [ ] `.autochip_api_keys.py` **不在** `git status` 输出中
- [ ] `outputs/` 目录**不在** `git status` 输出中
- [ ] 运行 `git check-ignore AutoChip/.autochip_api_keys.py` 有输出
- [ ] 已阅读并理解 [API_KEYS_SECURITY_GUIDE.md](AutoChip/API_KEYS_SECURITY_GUIDE.md)
- [ ] 团队成员都知道如何配置自己的API密钥
- [ ] 已测试新配置能正常运行

---

**祝你在GitHub上分享AutoChip项目顺利！** 🎉

如有问题，请查阅：
- [API密钥安全配置指南](AutoChip/API_KEYS_SECURITY_GUIDE.md)
- [快速参考卡片](AutoChip/QUICK_START_SECURITY.md)
- [参数化批量测试指南](docs/参数化批量测试快速参考.md)