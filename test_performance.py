import os
import time
import random
from memory_profiler import profile
from aegis_log import stream_log_files, sample_log_lines

def generate_test_log(file_path, num_lines=10000):
    """生成测试日志文件"""
    with open(file_path, 'w') as f:
        for i in range(num_lines):
            ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            f.write(f"[2025-08-22 12:34:56] {ip} - GET /test HTTP/1.1\n")

@profile
def test_streaming_memory(file_path, batch_size=100):
    """测试流式读取内存使用"""
    start_time = time.time()
    line_count = 0
    
    for line in stream_log_files():
        line_count += 1
        if line_count % batch_size == 0:
            print(f"Processed {line_count} lines", end='\r')
    
    print(f"\nTotal lines: {line_count}")
    print(f"Time taken: {time.time() - start_time:.2f}s")

@profile
def test_tail_mode(file_path):
    """测试tail模式响应"""
    print("Starting tail mode test...")
    line_count = 0
    
    for line in stream_log_files(tail_mode=True):
        line_count += 1
        print(f"New line detected: {line[:50]}...")
        
        if line_count >= 5:  # 测试5行后退出
            break

def run_performance_tests():
    """运行所有性能测试"""
    test_file = "test_performance.log"
    
    # 生成测试文件
    print("Generating test log file...")
    generate_test_log(test_file, 100000)  # 10万行测试数据
    
    # 设置测试环境
    os.environ['ANALYZE_FILES'] = test_file
    
    # 测试1: 流式读取内存效率
    print("\n=== Testing streaming memory efficiency ===")
    test_streaming_memory(test_file)
    
    # 测试2: 不同batch_size性能
    print("\n=== Testing different batch sizes ===")
    for size in [10, 100, 1000]:
        print(f"\nBatch size: {size}")
        start = time.time()
        batches = sample_log_lines(batch_size=size)
        print(f"Processed {sum(len(b) for b in batches)} lines in {time.time()-start:.2f}s")
    
    # 测试3: tail模式
    print("\n=== Testing tail mode ===")
    test_tail_mode(test_file)

if __name__ == "__main__":
    run_performance_tests()