# 🔐 AutoChip API密钥安全配置 - 快速参考

## ⚡ 30秒快速配置

```bash
# 1. 复制示例文件
cp .autochip_api_keys.example.py .autochip_api_keys.py

# 2. 编辑并填入真实密钥
vim .autochip_api_keys.py

# 3. 完成！开始使用
conda run -n autochip python autochip_scripts/run_batch_experiments.py -g hard -l 3 -i 2 -k 2 --mixed-models -n test
```

---

## 📝 配置文件示例

`.autochip_api_keys.py`:
```python
SILICONFLOW_CONFIG = {
    'api_key': 'sk-your-real-key-here',  # ← 替换
    'base_url': 'https://api.siliconflow.cn/v1'
}

GITHUB_CONFIG = {
    'api_key': 'ghp-your-real-token-here',  # ← 替换
    'base_url': 'https://models.inference.ai.azure.com'
}
```

---

## ✅ 安全检查清单

提交到GitHub前确认：

- [ ] `.autochip_api_keys.py` **不在** `git status` 输出中
- [ ] `.autochip_api_keys.example.py` **在** Git中（占位符版本）
- [ ] `.gitignore` 包含 `.autochip_api_keys.py`
- [ ] 代码中没有硬编码的真实密钥

验证命令：
```bash
git status | grep ".autochip_api_keys.py"
# 应该没有输出 ✅
```

---

## 🆘 紧急情况

### 不小心提交了密钥？

```bash
# 1. 立即在API提供商处撤销密钥
# 2. 生成新密钥
# 3. 清理Git历史
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .autochip_api_keys.py' \
  --prune-empty --tag-name-filter cat -- --all

# 4. 强制推送
git push origin --force --all
```

---

## 📚 详细文档

- [API_KEYS_SECURITY_GUIDE.md](API_KEYS_SECURITY_GUIDE.md) - 完整安全指南
- [docs/参数化批量测试快速参考.md](docs/参数化批量测试快速参考.md) - 使用指南

---

**记住**: `.autochip_api_keys.py` = 🔒 私密 | `.autochip_api_keys.example.py` = 🌐 公开
