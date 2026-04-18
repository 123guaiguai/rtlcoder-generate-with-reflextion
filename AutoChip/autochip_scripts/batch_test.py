#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoChip 批量测试脚本 - 支持断点续传和分组测试
功能：
1. 将测试集分为简单（0-50题）和困难（50-100题）两组
2. 每组独立运行，支持断点续传
3. 迭代次数限制为 2 次（共尝试 3 次：iter0, iter1, iter2）
4. 详细统计日志记录通过率
5. 支持后台运行，防止 SSH 断联
"""

import os
import sys
import json
import subprocess
import time
import glob
import re
from datetime import datetime
from pathlib import Path

# 配置参数
VERILOG_EVAL_DIR = "../VerilogEval"
OUTPUT_BASE_DIR = "outputs/batch_tests"
CONFIG_TEMPLATE = "configs/config_batch_test.json"
NUM_CANDIDATES = 3  # 每个迭代生成3个候选，用于验证多候选评估机制

# 分组配置（不同组使用不同的迭代次数和模型策略）
GROUP_CONFIGS = {
    "easy": {
        "range": (0, 50),
        "max_iterations": 2,  # 简单组：3次迭代（iter0, iter1, iter2）
        "use_mixed_models": False,
        "model_family": "Siliconflow",
        "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct"
    },
    "hard": {
        "range": (50, 100),
        "max_iterations": 5,  # 困难组：执行 iter0-iter4（共5次），iter5 使用 GPT-4o-mini
        "use_mixed_models": True,  # 启用混合模型
        # 混合模型配置：前5次用Qwen-32B（Siliconflow），最后1次用GPT-4o-mini（GitHub Models）
        "mixed_models": {
            "model1": {
                "start_iteration": 0,
                "model_family": "Siliconflow",
                "model_id": "Qwen/Qwen2.5-Coder-32B-Instruct"
            },
            "model2": {
                "start_iteration": 5,  # 第6次迭代（iter5）使用GPT-4o-mini
                "model_family": "ChatGPT",
                "model_id": "gpt-4o-mini",
                "base_url": "https://models.inference.ai.azure.com"  # GitHub Models API 端点
            }
        }
    }
}


def get_problem_list():
    """获取所有测试题列表"""
    prompt_files = sorted(glob.glob(os.path.join(VERILOG_EVAL_DIR, "Prob*_prompt.txt")))
    problems = []
    for pf in prompt_files:
        basename = os.path.basename(pf)
        # 提取题目编号，如 Prob001_zero_prompt.txt -> Prob001_zero
        prob_id = basename.replace("_prompt.txt", "")
        problems.append(prob_id)
    
    print(f"📋 找到 {len(problems)} 道题目")
    if problems:
        print(f"   第一题: {problems[0]}")
        print(f"   最后一题: {problems[-1]}")
    
    return problems


def split_problems_into_groups(problems):
    """将题目按编号分为简单和困难两组"""
    groups = {name: [] for name in GROUP_CONFIGS}
    
    parse_errors = 0
    for prob in problems:
        # 提取数字部分，如 Prob001_zero -> 001 -> 1
        # 格式：Prob + 3位数字 + _ + 名称
        try:
            # 从 "Prob" 之后提取，取前3个字符作为编号
            num_str = prob[4:7]  # Prob001_zero -> "001"
            num = int(num_str)
        except (ValueError, IndexError) as e:
            print(f"⚠️  警告: 无法解析题目编号: {prob} ({e})")
            parse_errors += 1
            continue
        
        assigned = False
        for group_name, config in GROUP_CONFIGS.items():
            start, end = config["range"]
            if start <= num < end:
                groups[group_name].append(prob)
                assigned = True
                break
        
        if not assigned:
             # 可以选择忽略或归入其他组，这里暂时忽略超出范围的题目
             pass
    
    if parse_errors > 0:
        print(f"⚠️  共有 {parse_errors} 道题目解析失败")
    
    print(f"📊 分组完成:")
    for group_name, config in GROUP_CONFIGS.items():
        start, end = config["range"]
        print(f"   {group_name.capitalize()}组 ({start}-{end-1}): {len(groups[group_name])} 道题")
    
    return groups


def create_config_for_problem(prob_id, output_dir, group_name):
    """为单个问题创建配置文件"""
    if group_name not in GROUP_CONFIGS:
        raise ValueError(f"未知的组名: {group_name}")
    
    group_cfg = GROUP_CONFIGS[group_name]
    
    # output_dir 已经包含了 prob_id，直接使用
    full_output_dir = output_dir
    
    general_config = {
        "prompt": f"{VERILOG_EVAL_DIR}/{prob_id}_prompt.txt",
        "name": "TopModule",
        "testbench": f"{VERILOG_EVAL_DIR}/{prob_id}_test.sv",
        "model_family": group_cfg.get("model_family", "Siliconflow"),
        "model_id": group_cfg.get("model_id", ""),
        "num_candidates": NUM_CANDIDATES,
        "iterations": group_cfg["max_iterations"],
        "outdir": full_output_dir,
        "log": "log.txt",
        "mixed-models": group_cfg.get("use_mixed_models", False)
    }
    
    config_data = {
        "general": general_config
    }
    
    # 如果启用混合模型，添加 mixed-models 配置
    if group_cfg.get("use_mixed_models", False) and "mixed_models" in group_cfg:
        config_data["mixed-models"] = group_cfg["mixed_models"]
    else:
        config_data["mixed-models"] = {}
    
    # 确保 configs 目录存在
    os.makedirs("configs", exist_ok=True)
    config_file = f"configs/config_{prob_id}.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=4)
    
    return config_file


def check_if_completed(output_dir):
    """
    检查某个题目是否已经完成测试
    
    修复说明：
    - 之前错误地检查 iter*/response*/log.txt（这些文件不包含最终Rank）
    - 现在正确读取 output_dir/log.txt（主日志文件包含最终Rank）
    
    Returns:
        tuple: (completed: bool, rank: float or None)
    """
    # 主日志文件路径
    main_log = os.path.join(output_dir, "log.txt")
    
    if not os.path.exists(main_log):
        return False, None
    
    try:
        with open(main_log, 'r') as f:
            content = f.read()
            
            # 查找 "Rank of best response: X.XX" （标准格式）
            rank_match = re.search(r'Rank of best response:\s*([-\d.]+)', content)
            if rank_match:
                rank = float(rank_match.group(1))
                return True, rank
            
            # 备用格式1: "Best.*Rank: X.XX"
            rank_match = re.search(r'Best.*Rank:\s*([-\d.]+)', content)
            if rank_match:
                rank = float(rank_match.group(1))
                return True, rank
            
            # 备用格式2: "Final Rank: X.XX"
            rank_match = re.search(r'Final Rank:\s*([-\d.]+)', content)
            if rank_match:
                rank = float(rank_match.group(1))
                return True, rank
            
            # 如果找到了迭代记录但没有Rank，说明测试未完成或出错
            if "Iteration:" in content:
                # 测试已开始但未完成
                return False, None
            
    except Exception as e:
        print(f"⚠️ 读取日志文件失败 {main_log}: {e}")
    
    return False, None


def run_single_test(prob_id, config_file, output_dir):
    """运行单个测试"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {prob_id}")
    print(f"{'='*60}")
    
    # 检查是否已完成
    completed, rank = check_if_completed(output_dir)
    if completed:
        status = "✅ PASS" if rank == 1.0 else "❌ FAIL"
        print(f"⏭️  跳过（已完成）: {status} (Rank: {rank})")
        return rank
    
    # 构建命令
    cmd = [
        "python", "generate_verilog.py",
        "-c", config_file
    ]
    
    print(f"🚀 开始测试...")
    start_time = time.time()
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
        # 取消所有代理设置（包括SOCKS代理）
        env.pop('http_proxy', None)
        env.pop('https_proxy', None)
        env.pop('all_proxy', None)
        env.pop('HTTP_PROXY', None)
        env.pop('HTTPS_PROXY', None)
        env.pop('ALL_PROXY', None)
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            print(f"❌ 执行失败 (返回码: {result.returncode})")
            if result.stderr:
                print(f"错误信息: {result.stderr[:500]}")
            return -1
        
        # 检查输出
        completed, rank = check_if_completed(output_dir)
        if completed:
            status = "✅ PASS" if rank == 1.0 else "❌ FAIL"
            print(f"✅ 完成 ({elapsed:.1f}s): {status} (Rank: {rank})")
            return rank
        else:
            print(f"❌ 完成但未找到结果")
            return -1
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 超时 (>10分钟)")
        return -2
    except Exception as e:
        print(f"❌ 异常: {e}")
        return -3


def run_group(group_name, problems, summary_log):
    """运行一组测试"""
    print(f"\n{'#'*80}")
    print(f"# 📊 开始测试组: {group_name.upper()} ({len(problems)} 道题)")
    print(f"# {'#'*78}")
    
    results = []
    passed = 0
    failed = 0
    skipped = 0
    errors = 0
    
    group_start_time = time.time()
    
    for i, prob_id in enumerate(problems, 1):
        print(f"\n[{i}/{len(problems)}] ", end="")
        
        # 创建输出目录
        output_dir = f"{OUTPUT_BASE_DIR}/{group_name}/{prob_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建配置文件
        config_file = create_config_for_problem(prob_id, output_dir, group_name)
        
        # 运行测试
        rank = run_single_test(prob_id, config_file, output_dir)
        
        results.append({
            "problem": prob_id,
            "rank": rank,
            "status": "PASS" if rank == 1.0 else "FAIL" if rank >= 0 else "ERROR"
        })
        
        if rank == 1.0:
            passed += 1
        elif rank >= 0:
            failed += 1
        elif rank == -1:
            skipped += 1
        else:
            errors += 1
        
        # 实时写入进度
        summary_log.write(f"[{group_name}] [{i}/{len(problems)}] {prob_id}: Rank={rank}\n")
        summary_log.flush()
    
    group_elapsed = time.time() - group_start_time
    
    # 计算统计信息
    total = len(problems)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    stats = {
        "group": group_name,
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "pass_rate": pass_rate,
        "elapsed_time": group_elapsed
    }
    
    # 写入统计日志
    summary_log.write(f"\n{'='*80}\n")
    summary_log.write(f"📊 {group_name.upper()} 组测试结果统计\n")
    summary_log.write(f"{'='*80}\n")
    summary_log.write(f"总题数:     {total}\n")
    summary_log.write(f"通过数:     {passed} ✅\n")
    summary_log.write(f"失败数:     {failed} ❌\n")
    summary_log.write(f"跳过数:     {skipped} ⏭️\n")
    summary_log.write(f"错误数:     {errors} ⚠️\n")
    summary_log.write(f"通过率:     {pass_rate:.2f}%\n")
    summary_log.write(f"耗时:       {group_elapsed:.1f} 秒 ({group_elapsed/60:.1f} 分钟)\n")
    summary_log.write(f"{'='*80}\n\n")
    summary_log.flush()
    
    # 打印总结
    print(f"\n{'='*80}")
    print(f"📊 {group_name.upper()} 组测试完成")
    print(f"{'='*80}")
    print(f"总题数:   {total}")
    print(f"通过:     {passed} ✅")
    print(f"失败:     {failed} ❌")
    print(f"跳过:     {skipped} ⏭️")
    print(f"错误:     {errors} ⚠️")
    print(f"通过率:   {pass_rate:.2f}%")
    print(f"耗时:     {group_elapsed:.1f}s ({group_elapsed/60:.1f}min)")
    print(f"{'='*80}")
    
    return stats, results


def main():
    """主函数"""
    print("="*80)
    print("🚀 AutoChip 批量测试系统")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"候选数量: {NUM_CANDIDATES}")
    print(f"分组配置:")
    for g_name, g_cfg in GROUP_CONFIGS.items():
        print(f"  - {g_name}: 迭代={g_cfg['max_iterations']}, 混合模型={g_cfg.get('use_mixed_models', False)}")
    print("="*80)
    
    # 创建输出目录
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # 创建汇总日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_log_path = f"{OUTPUT_BASE_DIR}/summary_{timestamp}.log"
    summary_log = open(summary_log_path, 'w')
    
    summary_log.write("="*80 + "\n")
    summary_log.write("AutoChip 批量测试汇总日志\n")
    summary_log.write("="*80 + "\n")
    summary_log.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    summary_log.write(f"候选数量: {NUM_CANDIDATES}\n")
    summary_log.write(f"分组配置:\n")
    for g_name, g_cfg in GROUP_CONFIGS.items():
        summary_log.write(f"  - {g_name}: 迭代={g_cfg['max_iterations']}, 混合模型={g_cfg.get('use_mixed_models', False)}\n")
    summary_log.write("="*80 + "\n\n")
    summary_log.flush()
    
    try:
        # 获取所有题目
        print("\n📋 加载测试题列表...")
        all_problems = get_problem_list()
        print(f"✅ 找到 {len(all_problems)} 道题目")
        
        # 分组
        print("\n📊 分组测试题...")
        groups = split_problems_into_groups(all_problems)
        print(f"✅ 简单组 (0-50): {len(groups['easy'])} 道题")
        print(f"✅ 困难组 (50-100): {len(groups['hard'])} 道题")
        
        # 写入分组信息
        summary_log.write(f"\n测试分组:\n")
        summary_log.write(f"  简单组 (0-50): {len(groups['easy'])} 道题\n")
        summary_log.write(f"  困难组 (50-100): {len(groups['hard'])} 道题\n\n")
        summary_log.flush()
        
        # 运行测试
        all_stats = []
        all_results = []
        
        overall_start = time.time()
        
        for group_name in ["hard"]:
        # for group_name in ["easy", "hard"]:
            problems = groups[group_name]
            if not problems:
                print(f"\n⚠️  {group_name} 组没有题目，跳过")
                continue
            
            stats, results = run_group(group_name, problems, summary_log)
            all_stats.append(stats)
            all_results.extend(results)
        
        overall_elapsed = time.time() - overall_start
        
        # 总体统计
        total_passed = sum(s["passed"] for s in all_stats)
        total_failed = sum(s["failed"] for s in all_stats)
        total_skipped = sum(s["skipped"] for s in all_stats)
        total_errors = sum(s["errors"] for s in all_stats)
        total_problems = sum(s["total"] for s in all_stats)
        overall_pass_rate = (total_passed / total_problems * 100) if total_problems > 0 else 0
        
        # 写入总体统计
        summary_log.write("\n" + "="*80 + "\n")
        summary_log.write("🎯 总体测试结果\n")
        summary_log.write("="*80 + "\n")
        summary_log.write(f"总题数:     {total_problems}\n")
        summary_log.write(f"总通过:     {total_passed} ✅\n")
        summary_log.write(f"总失败:     {total_failed} ❌\n")
        summary_log.write(f"总跳过:     {total_skipped} ⏭️\n")
        summary_log.write(f"总错误:     {total_errors} ⚠️\n")
        summary_log.write(f"总体通过率: {overall_pass_rate:.2f}%\n")
        summary_log.write(f"总耗时:     {overall_elapsed:.1f} 秒 ({overall_elapsed/3600:.2f} 小时)\n")
        summary_log.write("="*80 + "\n")
        summary_log.write(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        summary_log.flush()
        
        # 打印总体统计
        print(f"\n{'#'*80}")
        print(f"# 🎯 总体测试结果")
        print(f"{'#'*80}")
        print(f"总题数:     {total_problems}")
        print(f"总通过:     {total_passed} ✅")
        print(f"总失败:     {total_failed} ❌")
        print(f"总跳过:     {total_skipped} ⏭️")
        print(f"总错误:     {total_errors} ⚠️")
        print(f"总体通过率: {overall_pass_rate:.2f}%")
        print(f"总耗时:     {overall_elapsed:.1f}s ({overall_elapsed/3600:.2f}h)")
        print(f"{'#'*80}")
        
        print(f"\n📄 详细日志已保存到: {summary_log_path}")
        
    finally:
        summary_log.close()
    
    print("\n✅ 批量测试完成！")


if __name__ == "__main__":
    main()
