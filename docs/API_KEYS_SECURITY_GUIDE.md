# AutoChip API密钥安全配置指南

## 🔐 安全架构说明

为了保护API密钥不被泄露到GitHub，AutoChip采用**外部配置文件 + .gitignore**的安全方案。

---

## 📁 文件结构

```
AutoChip/
├── .autochip_api_keys.py              # ⚠️ 真实密钥（已加入.gitignore，不会上传）
├── .autochip_api_keys.example.py      # ✅ 示例模板（可以上传到GitHub）
├── .gitignore                         # ✅ Git忽略规则
└── autochip_scripts/
    └── languagemodels.py              # 从外部文件读取密钥
```

---

## 🚀 快速开始

### 1️⃣ 首次使用配置

```bash
cd /home/gq/Autochip_workspace/AutoChip

# 复制示例文件
cp .autochip_api_keys.example.py .autochip_api_keys.py

# 编辑配置文件，填入真实密钥
nano .autochip_api_keys.py
# 或
vim .autochip_api_keys.py
```

### 2️⃣ 编辑配置文件

打开 `.autochip_api_keys.py`，修改以下内容：

```python
# Siliconflow (硅基流动) API配置
SILICONFLOW_CONFIG = {
    'api_key': 'sk-your-real-api-key-here',  # ← 替换为你的真实密钥
    'base_url': 'https://api.siliconflow.cn/v1'
}

# GitHub Models API配置
GITHUB_CONFIG = {
    'api_key': 'ghp-your-real-token-here',  # ← 替换为你的真实Token
    'base_url': 'https://models.inference.ai.azure.com'
}
```

### 3️⃣ 验证配置

```bash
cd autochip_scripts
conda run -n autochip python generate_verilog.py \
    -c configs/config_Prob050_kmap1.json \
    -o outputs/test_config/Prob050
```

如果看到正常的运行日志，说明配置成功！✅

---

## 🛡️ 安全机制

### 1. `.gitignore` 保护

以下文件已被添加到 `.gitignore`，**不会被提交到Git仓库**：

```gitignore
.autochip_api_keys.py          # 真实密钥文件
.autochip_config.json          # 可能的本地配置
*.env                          # 环境变量文件
```

### 2. 示例文件公开

`.autochip_api_keys.example.py` 可以安全地提交到GitHub，因为它只包含占位符：

```python
SILICONFLOW_CONFIG = {
    'api_key': 'sk-your-siliconflow-api-key-here',  # 占位符，非真实密钥
    'base_url': 'https://api.siliconflow.cn/v1'
}
```

### 3. 代码中无硬编码

`languagemodels.py` 不再包含任何真实的API密钥，而是动态加载外部配置文件。

---

## ⚠️ 重要注意事项

### ❌ 禁止操作

1. **永远不要**将 `.autochip_api_keys.py` 添加到Git
2. **永远不要**在代码中硬编码真实API密钥
3. **永远不要**在公开场合（如截图、日志）展示完整密钥
4. **永远不要**通过邮件、聊天软件明文发送密钥

### ✅ 推荐做法

1. **定期轮换密钥**：每3-6个月更新一次API密钥
2. **使用环境变量备份**：在服务器部署时可使用环境变量作为备选
3. **限制密钥权限**：仅授予必要的API访问权限
4. **监控使用情况**：定期检查API使用日志，发现异常立即撤销密钥

---

## 🔧 高级配置选项

### 方案A：多环境配置（开发/生产）

```python
# .autochip_api_keys.py
import os

ENV = os.getenv('AUTOCHIP_ENV', 'development')

if ENV == 'production':
    SILICONFLOW_CONFIG = {
        'api_key': os.getenv('SILICONFLOW_API_KEY_PROD'),
        'base_url': 'https://api.siliconflow.cn/v1'
    }
else:
    SILICONFLOW_CONFIG = {
        'api_key': 'sk-dev-key-here',
        'base_url': 'https://api.siliconflow.cn/v1'
    }
```

### 方案B：密钥管理服务（企业级）

对于团队协作，建议使用专业的密钥管理服务：

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Cloud Secret Manager**

---

## 🆘 常见问题

### Q1: 忘记创建配置文件会怎样？

**A**: 程序会抛出清晰的错误提示：
```
❌ 错误: 未找到API密钥配置文件 .autochip_api_keys.py
   请按以下步骤配置:
   1. 复制示例文件: cp .autochip_api_keys.example.py .autochip_api_keys.py
   2. 编辑 .autochip_api_keys.py，填入你的真实API密钥
   3. ⚠️ 不要将 .autochip_api_keys.py 提交到Git仓库
```

### Q2: 如何确认密钥文件没有被Git跟踪？

**A**: 运行以下命令检查：
```bash
git status | grep ".autochip_api_keys.py"
# 如果没有输出，说明文件未被跟踪 ✅
```

### Q3: 不小心提交了密钥怎么办？

**A**: 立即执行以下步骤：
1. **撤销密钥**：在API提供商控制台立即撤销该密钥
2. **生成新密钥**：创建新的API密钥
3. **清理Git历史**：
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .autochip_api_keys.py' \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **强制推送**：
   ```bash
   git push origin --force --all
   ```
5. **通知团队**：告知所有协作者重新克隆仓库

### Q4: 团队协作时如何共享配置？

**A**: 
- **方式1**：每个成员独立创建自己的 `.autochip_api_keys.py`
- **方式2**：使用团队共享的密钥管理服务（推荐）
- **方式3**：通过安全的密码管理工具（如1Password、LastPass）分享

---

## 📊 安全对比

| 方案 | 安全性 | 便利性 | 适用场景 |
|------|--------|--------|----------|
| **硬编码在代码中** ❌ | 极低 | 高 | 不推荐 |
| **环境变量** ⚠️ | 中 | 中 | 服务器部署 |
| **外部配置文件 + .gitignore** ✅ | 高 | 高 | **个人开发（当前方案）** |
| **密钥管理服务** 🏆 | 极高 | 中 | 企业团队 |

---

## 📝 检查清单

在提交代码到GitHub之前，请确认：

- [ ] `.autochip_api_keys.py` 已添加到 `.gitignore`
- [ ] 代码中没有硬编码的真实API密钥
- [ ] `.autochip_api_keys.example.py` 已创建并包含占位符
- [ ] 运行 `git status` 确认敏感文件未被跟踪
- [ ] 测试程序能正常从配置文件加载密钥

---

## 🔗 相关资源

- [GitHub官方：移除敏感数据](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP密钥管理最佳实践](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [12-Factor App：配置](https://12factor.net/zh_cn/config)

---

**最后更新**: 2026-04-18  
**维护者**: AutoChip Team