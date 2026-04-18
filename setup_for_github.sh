#!/bin/bash
# AutoChip Workspace - GitHub上传准备脚本
# 此脚本帮助你安全地准备项目上传到GitHub

set -e

echo "================================================================================"
echo "🚀 AutoChip Workspace - GitHub上传准备"
echo "================================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "AutoChip/autochip_scripts/languagemodels.py" ]; then
    echo -e "${RED}❌ 错误: 请在 /home/gq/Autochip_workspace 目录下运行此脚本${NC}"
    exit 1
fi

echo "步骤 1/5: 检查Git仓库..."
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  未检测到Git仓库，正在初始化...${NC}"
    git init
    echo -e "${GREEN}✅ Git仓库已初始化${NC}"
else
    echo -e "${GREEN}✅ Git仓库已存在${NC}"
fi
echo ""

echo "步骤 2/5: 检查.gitignore配置..."
if [ ! -f ".gitignore" ]; then
    echo -e "${RED}❌ 错误: .gitignore文件不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ .gitignore文件存在${NC}"
echo ""

echo "步骤 3/5: 检查API密钥配置文件..."
if [ -f "AutoChip/.autochip_api_keys.py" ]; then
    echo -e "${GREEN}✅ API密钥配置文件存在${NC}"
    
    # 验证是否被.gitignore忽略
    if git check-ignore -q AutoChip/.autochip_api_keys.py; then
        echo -e "${GREEN}✅ API密钥文件已被正确忽略${NC}"
    else
        echo -e "${RED}❌ 警告: API密钥文件未被.gitignore忽略！${NC}"
        echo "   请检查 .gitignore 是否包含: AutoChip/.autochip_api_keys.py"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  API密钥配置文件不存在${NC}"
    echo "   如果你需要运行代码，请执行:"
    echo "   cp AutoChip/.autochip_api_keys.example.py AutoChip/.autochip_api_keys.py"
    echo "   然后编辑 AutoChip/.autochip_api_keys.py 填入真实密钥"
fi
echo ""

echo "步骤 4/5: 清理大型输出文件..."
if [ -d "AutoChip/autochip_scripts/outputs" ]; then
    OUTPUT_SIZE=$(du -sh AutoChip/autochip_scripts/outputs 2>/dev/null | cut -f1)
    echo -e "${YELLOW}⚠️  发现输出目录，大小: ${OUTPUT_SIZE}${NC}"
    echo "   这些文件不会被提交到Git（已在.gitignore中排除）"
else
    echo -e "${GREEN}✅ 输出目录不存在或为空${NC}"
fi
echo ""

echo "步骤 5/5: 生成Git状态报告..."
echo ""
echo "================================================================================"
echo "📊 Git状态报告"
echo "================================================================================"
echo ""

# 统计将被跟踪的文件
TRACKED_FILES=$(git ls-files 2>/dev/null | wc -l || echo "0")
echo "已跟踪文件数: $TRACKED_FILES"
echo ""

# 检查敏感文件
echo "敏感文件检查:"
if git ls-files | grep -q ".autochip_api_keys.py"; then
    echo -e "  ${RED}❌ .autochip_api_keys.py - 被跟踪（危险！）${NC}"
else
    echo -e "  ${GREEN}✅ .autochip_api_keys.py - 未被跟踪${NC}"
fi

if git ls-files | grep -q "outputs/"; then
    echo -e "  ${RED}❌ outputs/ 目录 - 被跟踪（不推荐）${NC}"
else
    echo -e "  ${GREEN}✅ outputs/ 目录 - 未被跟踪${NC}"
fi

if git ls-files | grep -q "\.log$"; then
    echo -e "  ${RED}❌ .log 文件 - 被跟踪（不推荐）${NC}"
else
    echo -e "  ${GREEN}✅ .log 文件 - 未被跟踪${NC}"
fi

echo ""
echo "================================================================================"
echo "✅ 准备完成！"
echo "================================================================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 添加远程仓库（首次）："
echo "   git remote add origin https://github.com/你的用户名/仓库名.git"
echo ""
echo "2. 查看所有待提交文件："
echo "   git status"
echo ""
echo "3. 提交并推送："
echo "   git add ."
echo "   git commit -m \"Initial commit\""
echo "   git push -u origin main"
echo ""
echo "⚠️  重要提醒："
echo "   - 确保 .autochip_api_keys.py 不在 git status 输出中"
echo "   - 查看 GITHUB_UPLOAD_GUIDE.md 获取详细指南"
echo "   - 查看 AutoChip/API_KEYS_SECURITY_GUIDE.md 了解安全最佳实践"
echo ""
echo "================================================================================"
