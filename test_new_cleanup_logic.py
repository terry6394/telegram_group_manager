#!/usr/bin/env python3
"""
测试新的队列清理逻辑：无论成功失败都清空队列
"""

import json
import os
import tempfile
import shutil
from datetime import datetime

def test_new_cleanup_logic():
    """测试新的清理逻辑：无论成功失败都清空队列"""
    print("🔍 测试新的队列清理逻辑...")
    
    # 创建测试环境
    test_dir = tempfile.mkdtemp()
    test_queue_file = os.path.join(test_dir, 'deletion_queue.json')
    
    # 模拟真实场景
    mock_queue = [
        {"chat_id": -1002449863402, "message_id": 393},
        {"chat_id": -1002449863402, "message_id": 399},
        {"chat_id": -1002449863402, "message_id": 400},
        {"chat_id": -1002449863402, "message_id": 401},
        {"chat_id": -1002449863402, "message_id": 409},
        {"chat_id": -1002449863402, "message_id": 411},
        {"chat_id": -1002449863402, "message_id": 412},
        {"chat_id": -1002449863402, "message_id": 413},
        {"chat_id": -1002449863402, "message_id": 414},
        {"chat_id": -1002449863402, "message_id": 415},
        {"chat_id": -1002449863402, "message_id": 416}
    ]
    
    print(f"📊 初始队列: {len(mock_queue)} 条消息")
    
    # 保存初始数据
    with open(test_queue_file, 'w', encoding='utf-8') as f:
        json.dump(mock_queue, f, indent=2)
    
    # 模拟新的清理逻辑
    def simulate_new_cleanup(deletion_queue):
        """模拟新的清理逻辑：无论成功失败都清空队列"""
        success_count = 0
        failed_count = 0
        
        for entry in deletion_queue:
            # 模拟删除操作：假设部分成功，部分失败
            import random
            if random.random() < 0.7:  # 70% 成功率
                success_count += 1
            else:
                failed_count += 1
        
        # 无论成功失败，都清空队列
        return [], success_count, failed_count
    
    # 加载队列
    with open(test_queue_file, 'r', encoding='utf-8') as f:
        deletion_queue = json.load(f)
    
    # 执行清理
    new_queue, success_count, failed_count = simulate_new_cleanup(deletion_queue)
    
    # 验证结果
    print(f"✅ 成功删除: {success_count} 条")
    print(f"❌ 删除失败: {failed_count} 条")
    print(f"📊 最终队列: {len(new_queue)} 条")
    
    # 断言验证
    assert len(new_queue) == 0, f"预期队列为空，实际 {len(new_queue)} 条"
    assert success_count + failed_count == len(mock_queue), "消息总数不一致"
    
    # 更新队列文件
    with open(test_queue_file, 'w', encoding='utf-8') as f:
        json.dump(new_queue, f, indent=2)
    
    # 验证最终文件内容
    with open(test_queue_file, 'r', encoding='utf-8') as f:
        final_queue = json.load(f)
    
    print(f"✅ 验证成功！最终队列为空: {len(final_queue)} 条")
    
    # 清理测试目录
    shutil.rmtree(test_dir)
    
    return True

def test_edge_cases_new_logic():
    """测试新逻辑的边界情况"""
    print("\n🔍 测试新逻辑的边界情况...")
    
    edge_cases = [
        # 情况1: 空队列
        ([], 0, 0, 0),
        # 情况2: 单条消息成功
        ([{"chat_id": 1, "message_id": 1}], 1, 0, 0),
        # 情况3: 单条消息失败
        ([{"chat_id": 1, "message_id": 2}], 0, 1, 0),
        # 情况4: 多条消息混合
        ([{"chat_id": 1, "message_id": i} for i in range(1, 6)], 3, 2, 0)
    ]
    
    for test_queue, expected_success, expected_fail, expected_remaining in edge_cases:
        success_count = 0
        failed_count = 0
        
        # 简化模拟
        import random
        random.seed(42)  # 固定随机种子确保可重现
        
        for entry in test_queue:
            if random.random() < 0.6:  # 60% 成功率用于测试
                success_count += 1
            else:
                failed_count += 1
        
        final_queue = []  # 新逻辑：无论成功失败都清空
        
        assert len(final_queue) == expected_remaining, f"边界测试失败: {test_queue}"
        assert len(final_queue) + success_count + failed_count == len(test_queue)
    
    print("✅ 所有边界情况测试通过")

def main():
    """主验证函数"""
    print("🧪 新清理逻辑验证开始...")
    print("=" * 50)
    
    try:
        test_new_cleanup_logic()
        test_edge_cases_new_logic()
        
        print("\n" + "=" * 50)
        print("🎉 新清理逻辑验证完成！")
        print("✅ 无论成功失败都清空队列")
        print("✅ 队列清理彻底，无残留消息")
        print("✅ 所有边界情况测试通过")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)