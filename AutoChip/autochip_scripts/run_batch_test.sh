#!/bin/bash
# AutoChip 批量测试 - 后台运行脚本
# 使用方法: nohup ./run_batch_test.sh > batch_test_output.log 2>&1 &

# 记录开始时间
START_TIME=$(date +%Y%m%d_%H%M%S)
LOG_FILE="batch_test_${START_TIME}.log"

echo "==========================================" | tee -a "$LOG_FILE"
echo "🚀 AutoChip 批量测试 - 启动" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 检查 API Keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: 未设置 OPENAI_API_KEY 环境变量（用于 Siliconflow）" | tee -a "$LOG_FILE"
    echo "请运行: export OPENAI_API_KEY='your_siliconflow_key'" | tee -a "$LOG_FILE"
    exit 1
fi

# 检查 GPT-4o-mini 的 API Key（如果使用混合模型）
if [ -z "$GPT4O_MINI_API_KEY" ]; then
    echo "⚠️  警告: 未设置 GPT4O_MINI_API_KEY 环境变量" | tee -a "$LOG_FILE"
    echo "   困难组将使用混合模型策略，最后一次迭代需要 GPT-4o-mini" | tee -a "$LOG_FILE"
    echo "   请运行: export GPT4O_MINI_API_KEY='your_openai_key'" | tee -a "$LOG_FILE"
    echo "   或者设置与 OPENAI_API_KEY 相同的值" | tee -a "$LOG_FILE"
    # 不退出，让用户有机会在运行时设置
else
    echo "🔑 GPT-4o-mini API Key: 已设置" | tee -a "$LOG_FILE"
fi

# 进入工作目录
cd "$(dirname "$0")"

echo "📁 工作目录: $(pwd)" | tee -a "$LOG_FILE"
echo "🔑 API Key: 已设置" | tee -a "$LOG_FILE"
echo "📝 日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 取消代理（避免网络问题）
unset http_proxy https_proxy all_proxy
echo "✅ 网络代理已清理" | tee -a "$LOG_FILE"

# 激活 conda 环境
echo "🐍 激活 conda 环境..." | tee -a "$LOG_FILE"

# 尝试多种方式激活 conda
CONDA_ACTIVATED=false

# 方法 1: 使用 conda init 初始化后的方式
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    if conda activate autochip 2>/dev/null; then
        CONDA_ACTIVATED=true
        echo "✅ Conda 环境激活成功 (miniconda3)" | tee -a "$LOG_FILE"
    fi
elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
    if conda activate autochip 2>/dev/null; then
        CONDA_ACTIVATED=true
        echo "✅ Conda 环境激活成功 (anaconda3)" | tee -a "$LOG_FILE"
    fi
fi

# 如果 conda 激活失败，尝试直接使用 conda run
if [ "$CONDA_ACTIVATED" = false ]; then
    echo "⚠️  conda activate 失败，尝试使用 conda run..." | tee -a "$LOG_FILE"
    if command -v conda &> /dev/null; then
        # 使用 conda run 直接运行
        echo "✅ 将使用 conda run 运行" | tee -a "$LOG_FILE"
        CONDA_RUN="conda run -n autochip"
    else
        echo "❌ 错误: 无法激活 conda 环境" | tee -a "$LOG_FILE"
        exit 1
    fi
else
    CONDA_RUN=""
fi

# 验证 Python 版本
if [ -n "$CONDA_RUN" ]; then
    PYTHON_VERSION=$($CONDA_RUN python --version 2>&1)
else
    PYTHON_VERSION=$(python --version 2>&1)
fi
echo "🐍 Python 版本: $PYTHON_VERSION" | tee -a "$LOG_FILE"

echo "✅ 环境准备完成" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🚀 开始批量测试..." | tee -a "$LOG_FILE"
echo "💡 提示: 可以使用 'tail -f $LOG_FILE' 查看实时进度" | tee -a "$LOG_FILE"
echo "💡 提示: 可以使用 'ps aux | grep batch_test' 查看进程状态" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 设置 GPT-4o-mini 的 API Key（如果已设置）
if [ -n "$GPT4O_MINI_API_KEY" ]; then
    export OPENAI_API_KEY="$GPT4O_MINI_API_KEY"
    echo "🔑 使用 GPT-4o-mini API Key 进行最后一次迭代" | tee -a "$LOG_FILE"
fi

# 运行批量测试（所有输出都重定向到日志文件）
if [ -n "$CONDA_RUN" ]; then
    echo "🚀 执行命令: $CONDA_RUN python batch_test.py" | tee -a "$LOG_FILE"
    $CONDA_RUN python batch_test.py >> "$LOG_FILE" 2>&1
else
    echo "🚀 执行命令: python batch_test.py" | tee -a "$LOG_FILE"
    python batch_test.py >> "$LOG_FILE" 2>&1
fi

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 批量测试完成 (退出码: $EXIT_CODE)" | tee -a "$LOG_FILE"
else
    echo "❌ 批量测试失败 (退出码: $EXIT_CODE)" | tee -a "$LOG_FILE"
fi
echo "==========================================" | tee -a "$LOG_FILE"
echo "📄 完整日志: $LOG_FILE" | tee -a "$LOG_FILE"

exit $EXIT_CODE
