#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoChip 参数化批量测试工具
支持命令行参数控制所有实验配置，无需修改代码
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_test import (
    get_problem_list,
    create_config_for_problem,
    run_single_test,
    GROUP_CONFIGS,
    OUTPUT_BASE_DIR,
    VERILOG_EVAL_DIR
)


def load_env_config(env_file):
    """从配置文件加载环境变量"""
    if not os.path.exists(env_file):
        print(f"Warning: env file not found: {env_file}")
        return {}
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                env_vars[key.strip()] = value
    
    return env_vars


def setup_environment(env_file=None, api_keys=None):
    """设置环境变量"""
    # 清理代理
    for var in ['http_proxy', 'https_proxy', 'all_proxy', 
                'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        os.environ.pop(var, None)
    
    # 从文件加载
    if env_file:
        env_vars = load_env_config(env_file)
        for key, value in env_vars.items():
            os.environ[key] = value
        print(f"[OK] Loaded environment variables from: {env_file}")
    
    # 从命令行参数加载
    if api_keys:
        for key, value in api_keys.items():
            os.environ[key] = value
        print(f"[OK] Set API Keys from command line")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AutoChip Parameterized Batch Testing Tool')
    
    parser.add_argument('--group', '-g', choices=['easy', 'hard', 'all'], default='hard')
    parser.add_argument('--limit', '-l', type=int, default=None)
    parser.add_argument('--iterations', '-i', type=int, default=None)
    parser.add_argument('--candidates', '-k', type=int, default=None)
    parser.add_argument('--mixed-models', '-m', action='store_true', default=None)
    parser.add_argument('--no-mixed-models', action='store_true')
    parser.add_argument('--gpt-start-iter', type=int, default=None)
    parser.add_argument('--output-dir', '-o', type=str, default=None)
    parser.add_argument('--experiment-name', '-n', type=str, default=None)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--env-file', '-e', type=str, default=None)
    parser.add_argument('--api-key', action='append', nargs=2)
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    
    return parser.parse_args()


def generate_output_path(base_dir, group_name, experiment_name=None, overwrite=False):
    """生成输出目录路径"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if experiment_name:
        # 避免重复拼接group_name，如果experiment_name已经包含group_name则不再添加
        if group_name in experiment_name:
            dir_name = f"{experiment_name}_{timestamp}"
        else:
            dir_name = f"{experiment_name}_{group_name}_{timestamp}"
    else:
        dir_name = f"{group_name}_{timestamp}"
    
    output_path = os.path.join(base_dir, dir_name)
    
    if os.path.exists(output_path):
        if overwrite:
            print(f"Warning: Output directory exists, will overwrite: {output_path}")
            import shutil
            shutil.rmtree(output_path)
        else:
            completed = len([d for d in os.listdir(output_path) 
                           if os.path.isdir(os.path.join(output_path, d))])
            print(f"Info: Found existing output directory, resuming (completed {completed} problems)")
    
    os.makedirs(output_path, exist_ok=True)
    return output_path


def modify_group_config(group_name, config_updates):
    """动态修改组配置"""
    import copy
    modified_config = copy.deepcopy(GROUP_CONFIGS[group_name])
    
    if 'max_iterations' in config_updates:
        modified_config['max_iterations'] = config_updates['max_iterations']
    
    if 'use_mixed_models' in config_updates:
        modified_config['use_mixed_models'] = config_updates['use_mixed_models']
        
        # 如果禁用混合模型，需要从mixed_models.model1中提取model_id和model_family
        if not config_updates['use_mixed_models'] and 'mixed_models' in modified_config:
            model1 = modified_config['mixed_models'].get('model1', {})
            if 'model_family' in model1:
                modified_config['model_family'] = model1['model_family']
            if 'model_id' in model1:
                modified_config['model_id'] = model1['model_id']
    
    if 'mixed_models' in config_updates and config_updates['mixed_models']:
        mixed_cfg = config_updates['mixed_models']
        if 'model2' in modified_config.get('mixed_models', {}):
            if 'start_iteration' in mixed_cfg:
                modified_config['mixed_models']['model2']['start_iteration'] = mixed_cfg['start_iteration']
    
    return modified_config


def run_experiment(config):
    """运行实验"""
    print("="*80)
    print("AutoChip Parameterized Batch Testing")
    print("="*80)
    print()
    
    setup_environment(config['env_file'], config['api_keys'])
    print()
    
    groups_to_test = ['easy', 'hard'] if config['group'] == 'all' else [config['group']]
    all_problems = get_problem_list()
    
    for group_name in groups_to_test:
        print(f"\nPreparing test group: {group_name.upper()}")
        
        if group_name == 'easy':
            group_problems = [p for p in all_problems if p.startswith('Prob0') and int(p[4:7]) < 50]
        elif group_name == 'hard':
            group_problems = [p for p in all_problems if p.startswith('Prob0') and int(p[4:7]) >= 50]
        else:
            group_problems = all_problems
        
        if config['limit']:
            group_problems = group_problems[:config['limit']]
            print(f"Small-scale test mode: only testing first {config['limit']} problems")
        
        print(f"Problem count: {len(group_problems)}")
        
        output_base = generate_output_path(
            config['output_dir'], group_name, config['experiment_name'], config['overwrite']
        )
        print(f"Output directory: {output_base}")
        
        # Build config updates
        group_config_updates = {}
        if config['iterations'] is not None:
            group_config_updates['max_iterations'] = config['iterations']
        
        if config['mixed_models'] is not None:
            group_config_updates['use_mixed_models'] = config['mixed_models']
        elif config['disable_mixed_models']:
            group_config_updates['use_mixed_models'] = False
        
        if config['gpt_start_iter'] is not None:
            group_config_updates['mixed_models'] = {'start_iteration': config['gpt_start_iter']}
        
        import batch_test
        original_config = GROUP_CONFIGS[group_name].copy()
        original_candidates = batch_test.NUM_CANDIDATES
        
        modified_config = modify_group_config(group_name, group_config_updates)
        GROUP_CONFIGS[group_name] = modified_config
        
        if config['candidates'] is not None:
            batch_test.NUM_CANDIDATES = config['candidates']
        
        print(f"\nExperiment Configuration:")
        print(f"  - Iterations: {modified_config['max_iterations']} (will execute {modified_config['max_iterations']+1} times)")
        print(f"  - Candidates: {batch_test.NUM_CANDIDATES}")
        print(f"  - Mixed Models: {'Enabled' if modified_config.get('use_mixed_models') else 'Disabled'}")
        print()
        
        if config['dry_run']:
            print("Dry-run mode, skipping actual tests\n")
            GROUP_CONFIGS[group_name] = original_config
            batch_test.NUM_CANDIDATES = original_candidates
            continue
        
        results = []
        passed = failed = errors = skipped = 0
        start_time = time.time()
        
        for i, prob_id in enumerate(group_problems, 1):
            print(f"\n[{i}/{len(group_problems)}] ", end="")
            
            prob_output_dir = os.path.join(output_base, prob_id)
            
            log_file = os.path.join(prob_output_dir, "log.txt")
            if os.path.exists(log_file) and not config['overwrite']:
                try:
                    with open(log_file, 'r') as f:
                        if "Rank of best response:" in f.read():
                            print(f"Skipped (already completed)")
                            skipped += 1
                            continue
                except:
                    pass
            
            os.makedirs(prob_output_dir, exist_ok=True)
            config_file = create_config_for_problem(prob_id, prob_output_dir, group_name)
            rank = run_single_test(prob_id, config_file, prob_output_dir)
            
            results.append({'problem': prob_id, 'rank': rank})
            
            if rank == 1.0:
                passed += 1
            elif rank >= 0:
                failed += 1
            else:
                errors += 1
        
        elapsed = time.time() - start_time
        total = len(group_problems)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"{group_name.upper()} Group Test Results")
        print(f"{'='*80}")
        print(f"Total:      {total}")
        print(f"Passed:     {passed}")
        print(f"Failed:     {failed}")
        print(f"Skipped:    {skipped}")
        print(f"Errors:     {errors}")
        print(f"Pass Rate:  {pass_rate:.2f}%")
        print(f"Time:       {elapsed:.1f}s ({elapsed/60:.1f}min)")
        print(f"{'='*80}")
        
        result_file = os.path.join(output_base, f"results_{group_name}.json")
        result_data = {
            'timestamp': datetime.now().isoformat(),
            'group': group_name,
            'config': {
                'iterations': modified_config['max_iterations'],
                'candidates': batch_test.NUM_CANDIDATES,
                'mixed_models': modified_config.get('use_mixed_models', False),
            },
            'statistics': {
                'total': total, 'passed': passed, 'failed': failed,
                'skipped': skipped, 'errors': errors,
                'pass_rate': round(pass_rate, 2),
                'elapsed_seconds': round(elapsed, 1),
            },
            'details': results
        }
        
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"\nResults saved to: {result_file}")
        
        GROUP_CONFIGS[group_name] = original_config
        batch_test.NUM_CANDIDATES = original_candidates
    
    print("\nAll tests completed!")


def main():
    args = parse_args()
    config = {
        'group': args.group,
        'limit': args.limit,
        'iterations': args.iterations,
        'candidates': args.candidates,
        'mixed_models': args.mixed_models,
        'disable_mixed_models': args.no_mixed_models,
        'gpt_start_iter': args.gpt_start_iter,
        'output_dir': args.output_dir or OUTPUT_BASE_DIR,
        'experiment_name': args.experiment_name,
        'overwrite': args.overwrite,
        'env_file': args.env_file,
        'api_keys': dict(args.api_key) if args.api_key else {},
        'verbose': args.verbose,
        'dry_run': args.dry_run,
    }
    
    run_experiment(config)


if __name__ == '__main__':
    main()
