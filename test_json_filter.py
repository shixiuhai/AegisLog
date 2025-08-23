#!/usr/bin/env python3
import re

# 测试各种可能的JSON标签格式
test_cases = [
    '```json\n{"attack_ips": [{"ip": "1.2.3.4", "attack_type": "DDoS"}]}\n```',
    '```json {"attack_ips": [{"ip": "1.2.3.4", "attack_type": "DDoS"}]} ```',
    '```json\n{\n  "attack_ips": [\n    {\n      "ip": "1.2.3.4",\n      "attack_type": "DDoS"\n    }\n  ]\n}\n```',
    '没有标签的纯JSON: {"attack_ips": [{"ip": "1.2.3.4", "attack_type": "DDoS"}]}',
    '错误的标签格式: ```json{"attack_ips": [{"ip": "1.2.3.4", "attack_type": "DDoS"}]}```',
    '多行JSON带标签: ```json\n{\n    "attack_ips": [\n        {\n            "ip": "192.168.1.100",\n            "attack_type": "SQL Injection"\n        },\n        {\n            "ip": "10.0.0.1",\n            "attack_type": "XSS"\n        }\n    ]\n}\n```',
    '空JSON标签: ```json\n{}\n```',
    '只有开始标签: ```json\n{"test": "data"}',
    '只有结束标签: {"test": "data"}\n```',
]

pattern = r'```json\s*(.*?)\s*```'

print("测试JSON标签过滤功能:")
print("=" * 50)

for i, case in enumerate(test_cases, 1):
    print(f'\n测试用例 {i}: {case[:60]}...')
    match = re.search(pattern, case, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        print(f'  ✓ 匹配成功')
        print(f'  提取内容: {extracted[:80]}...')
        # 尝试解析JSON验证有效性
        try:
            import json
            parsed = json.loads(extracted)
            print(f'  ✓ JSON解析成功')
        except json.JSONDecodeError:
            print(f'  ✗ JSON解析失败')
    else:
        print('  ✗ 没有匹配到JSON标签')
    
    print('  ' + '-' * 40)

print("\n测试完成!")