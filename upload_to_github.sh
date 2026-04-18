#!/bin/bash
# AutoChip Workspace - 自动上传到GitHub脚本

set -e

echo "================================================================================"
echo "🚀 AutoChip Workspace - 上传到GitHub"
echo "================================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查是否在项目根目录
if [ ! -f "AutoChip/autochip_scripts/languagemodels.py" ]; then
    echo -e "${RED}❌ 错误: 请在 /home/gq/Autochip_workspace 目录下运行此脚本${NC}"
    exit 1
fi

echo -e "${BLUE}步骤 1/6: 配置Git用户信息${NC}"
echo ""
echo "请输入你的Git配置信息（这些信息会显示在你的提交记录中）："
echo ""

# 检查是否已配置
CURRENT_USER=$(git config user.name 2>/dev/null || echo "")
CURRENT_EMAIL=$(git config user.email 2>/dev/null || echo "")

if [ -n "$CURRENT_USER" ] && [ -n "$CURRENT_EMAIL" ]; then
    echo -e "当前配置:"
    echo -e "  用户名: ${GREEN}${CURRENT_USER}${NC}"
    echo -e "  邮箱: ${GREEN}${CURRENT_EMAIL}${NC}"
    echo ""
    read -p "是否使用当前配置？(y/n，默认y): " use_current
    if [ "$use_current" != "n" ]; then
        echo -e "${GREEN}✅ 使用现有配置${NC}"
    else
        read -p "请输入你的Git用户名: " git_user
        read -p "请输入你的Git邮箱: " git_email
        git config user.name "$git_user"
        git config user.email "$git_email"
        echo -e "${GREEN}✅ Git用户信息已更新${NC}"
    fi
else
    read -p "请输入你的Git用户名: " git_user
    read -p "请输入你的Git邮箱: " git_email
    git config user.name "$git_user"
    git config user.email "$git_email"
    echo -e "${GREEN}✅ Git用户信息已配置${NC}"
fi
echo ""

echo -e "${BLUE}步骤 2/6: 验证敏感文件保护${NC}"
echo ""

# 验证敏感文件
if git check-ignore -q AutoChip/.autochip_api_keys.py; then
    echo -e "${GREEN}✅ .autochip_api_keys.py 已被正确忽略${NC}"
else
    echo -e "${RED}❌ 警告: .autochip_api_keys.py 未被忽略！${NC}"
    exit 1
fi

if git ls-files | grep -q "outputs/"; then
    echo -e "${RED}❌ 警告: outputs/ 目录被跟踪！${NC}"
    exit 1
else
    echo -e "${GREEN}✅ outputs/ 目录未被跟踪${NC}"
fi
echo ""

echo -e "${BLUE}步骤 3/6: 添加文件到Git${NC}"
echo ""
git add .
echo -e "${GREEN}✅ 文件已添加到暂存区${NC}"
echo ""

echo -e "${BLUE}步骤 4/6: 创建首次提交${NC}"
echo ""
git commit -m "Initial commit: AutoChip workspace with secure API key management

- Add core AutoChip scripts and configurations
- Implement secure API key management with external config files
- Add batch testing and analysis tools
- Include comprehensive documentation
- Configure .gitignore to protect sensitive files"
echo -e "${GREEN}✅ 首次提交完成${NC}"
echo ""

echo -e "${BLUE}步骤 5/6: 配置远程仓库${NC}"
echo ""
echo "请输入你的GitHub仓库URL："
echo "格式: https://github.com/用户名/仓库名.git"
echo "或: git@github.com:用户名/仓库名.git"
echo ""
read -p "GitHub仓库URL: " repo_url

if [ -z "$repo_url" ]; then
    echo -e "${RED}❌ 错误: 仓库URL不能为空${NC}"
    exit 1
fi

# 检查是否已有remote
if git remote | grep -q "origin"; then
    echo -e "${YELLOW}⚠️  检测到已存在的origin远程仓库${NC}"
    read -p "是否覆盖？(y/n): " overwrite
    if [ "$overwrite" = "y" ]; then
        git remote remove origin
    else
        echo -e "${RED}❌ 取消操作${NC}"
        exit 1
    fi
fi

git remote add origin "$repo_url"
echo -e "${GREEN}✅ 远程仓库已配置: ${repo_url}${NC}"
echo ""

echo -e "${BLUE}步骤 6/6: 推送到GitHub${NC}"
echo ""
echo -e "${YELLOW}⚠️  即将推送代码到GitHub，请确认:${NC}"
echo -e "  远程仓库: ${GREEN}${repo_url}${NC}"
echo -e "  分支: ${GREEN}main${NC}"
echo ""
read -p "确认推送？(y/n): " confirm_push

if [ "$confirm_push" != "y" ]; then
    echo -e "${RED}❌ 取消推送${NC}"
    echo ""
    echo "你可以稍后手动执行:"
    echo "  git push -u origin main"
    exit 0
fi

echo ""
echo -e "${YELLOW}正在推送到GitHub...${NC}"
echo ""

# 尝试推送
if git push -u origin main; then
    echo ""
    echo -e "${GREEN}================================================================================${NC}"
    echo -e "${GREEN}🎉 成功！项目已上传到GitHub！${NC}"
    echo -e "${GREEN}================================================================================${NC}"
    echo ""
    echo "📊 项目地址: ${repo_url%.git}"
    echo ""
    echo "✅ 已完成:"
    echo "  • 所有代码和文档已上传"
    echo "  • 敏感文件(.autochip_api_keys.py)已排除"
    echo "  • 输出文件和日志已排除"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  • 确保 .autochip_api_keys.py 没有出现在GitHub仓库中"
    echo "  • 团队成员需要各自创建自己的API密钥配置文件"
    echo "  • 查看 GITHUB_UPLOAD_GUIDE.md 了解详细使用说明"
    echo ""
    echo "================================================================================"
else
    echo ""
    echo -e "${RED}❌ 推送失败！${NC}"
    echo ""
    echo "可能的原因:"
    echo "  1. 仓库不存在 - 请先在GitHub上创建空仓库"
    echo "  2. 认证失败 - 请检查GitHub访问令牌或SSH密钥"
    echo "  3. 网络问题 - 请检查网络连接"
    echo ""
    echo "你可以稍后重试:"
    echo "  git push -u origin main"
    exit 1
fi
