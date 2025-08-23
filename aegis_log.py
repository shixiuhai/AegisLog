import subprocess
import random
import time
import re
import json
import os
from openai import OpenAI
from config import (
    CHECK_INTERVAL, BLACKLIST_MAX, BATCH_SIZE,
    AI_API_URL, AI_API_KEY, CHAIN_NAME,
    AI_PROMPT_TEMPLATE,
    ANALYZE_FILES, USE_TAIL_COMMAND
)
from logger import AegisLogger
from models import db_manager

logger = AegisLogger()


# ================= iptables 管理 =================
class FirewallAI:
    def __init__(self):
        self.chain = CHAIN_NAME
        self.init_chain()

    def _run_cmd(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"命令失败: {e.stderr.strip()}")
            return None

    def init_chain(self):
        """初始化自定义黑名单链"""
        # FIX: 使用 `iptables -S` 精确判断链是否已存在，并确保 INPUT 链已跳转到自定义链
        rules = self._run_cmd("sudo iptables -S")
        if not rules:
            logger.error("无法获取 iptables 规则，跳过链初始化")
            return

        lines = rules.splitlines()
        has_chain = any(line.strip() == f"-N {self.chain}" for line in lines)
        if not has_chain:
            self._run_cmd(f"sudo iptables -N {self.chain}")
            logger.info(f"链 {self.chain} 已创建")
        else:
            logger.info(f"链 {self.chain} 已存在")

        # 确保 INPUT 有跳转到该链
        input_rules = [l for l in lines if l.startswith("-A INPUT ")]
        has_jump = any(f"-j {self.chain}" in l for l in input_rules)
        if not has_jump:
            self._run_cmd(f"sudo iptables -I INPUT -j {self.chain}")
            logger.info(f"链 {self.chain} 已加入 INPUT")
        else:
            logger.info(f"INPUT 已包含跳转到 {self.chain}")

    def add_ip(self, ip):
        """添加 IP 到黑名单"""
        if ip not in self.get_blacklist():
            self._run_cmd(f"sudo iptables -A {self.chain} -s {ip} -j DROP")
            logger.info(f"IP {ip} 加入黑名单")
            self.trim_blacklist()

    def remove_ip(self, ip):
        """从黑名单删除 IP"""
        # FIX: 基于 `iptables -S <chain>` 精确删除匹配规则，避免行号变化问题；并删除所有匹配项
        rules = self._run_cmd(f"sudo iptables -S {self.chain}")
        if not rules:
            logger.warning(f"无法获取链 {self.chain} 规则，删除 {ip} 失败")
            return

        removed_any = False
        for line in rules.splitlines():
            # 目标格式: -A CHAIN -s <ip>/32 -j DROP (可能还有其他匹配项)
            if line.startswith(f"-A {self.chain} ") and f"-s {ip}" in line and " -j DROP" in line:
                delete_cmd = "sudo iptables " + line.replace("-A", "-D", 1)
                out = self._run_cmd(delete_cmd)
                removed_any = True
        if removed_any:
            logger.info(f"IP {ip} 已删除")
        else:
            logger.info(f"未在 {self.chain} 找到 IP {ip} 的 DROP 规则")

    def get_blacklist(self):
        """返回当前黑名单 IP 列表"""
        # 仍使用 -n 列表，但修复提取 IP 的分组错误
        rules = self._run_cmd(f"sudo iptables -L {self.chain} -n")
        if not rules:
            return []
        ips = []
        for line in rules.splitlines():
            m = re.search(r"(\d{1,3}\.){3}\d{1,3}", line)
            if m:
                # FIX: group(0) 才是完整 IP
                ips.append(m.group(0))
        return ips

    def trim_blacklist(self):
        """保持黑名单不超过最大数量"""
        # FIX: 防止在删除失败时死循环；增加尝试上限并在无变化时中断
        attempts = 0
        max_attempts = 2 * max(1, BLACKLIST_MAX)  # 合理上限
        prev_len = None
        ips = self.get_blacklist()
        while len(ips) > BLACKLIST_MAX and attempts < max_attempts:
            prev_len = len(ips)
            # 按当前列表的“第一条”删（近似最早加入）；如果失败会触发保护逻辑
            self.remove_ip(ips[0])
            attempts += 1
            ips = self.get_blacklist()
            if len(ips) == prev_len:
                logger.warning("trim_blacklist 未能减少黑名单数量，可能删除失败，停止以避免死循环")
                break
        if len(ips) > BLACKLIST_MAX:
            logger.warning(f"黑名单长度仍为 {len(ips)}，超过上限 {BLACKLIST_MAX}，请检查规则删除是否受限")

# ================= 日志分析 =================
def sample_log_lines(batch_size=BATCH_SIZE):
    """遍历多个日志文件, 取出每个文件的最后 batch_size 行, 按批次返回
    Args:
        batch_size: 每批次的最大行数
    Returns:
        list[list[str]]: 每个子列表是一个批次的日志行
    """
    if not ANALYZE_FILES:
        return []

    file_paths = [path.strip() for path in ANALYZE_FILES.split(',')]
    batches = []

    for file_path in file_paths:
        if not os.path.exists(file_path):
            logger.warning(f"日志文件不存在: {file_path}")
            continue

        try:
            lines = []
            if USE_TAIL_COMMAND:
                # 使用 tail 命令直接读取文件最后 batch_size 行
                result = subprocess.run(
                    ['tail', '-n', str(batch_size), file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.splitlines()
                else:
                    logger.warning(f"tail 命令失败: {result.stderr}")

            # 如果没成功或禁用 tail, 使用 Python 读取
            if not lines:
                with open(file_path, 'r') as f:
                    lines = f.readlines()[-batch_size:]

            # 按 batch_size 分组
            current_batch = []
            for line in lines:
                current_batch.append(line.rstrip('\n'))
                if len(current_batch) >= batch_size:
                    batches.append(current_batch)
                    current_batch = []
            if current_batch:  # 加入最后不足 batch_size 的一批
                batches.append(current_batch)

        except Exception as e:
            logger.error(f"读取日志文件失败 {file_path}: {str(e)}")

    return batches

def analyze_lines_ai(lines):
    """一次发送多行日志给 AI 分析，返回攻击IP和类型信息"""
    # 准备日志内容
    log_content = "\n".join(lines)
    
    try:
        # 使用OpenAI SDK格式调用DeepSeek API
        client = OpenAI(
            api_key=AI_API_KEY,
            base_url=AI_API_URL,
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": AI_PROMPT_TEMPLATE},
                {"role": "user", "content": log_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )
        
        # 解析AI响应
        response_content = response.choices[0].message.content
        
        # 处理AI返回的JSON响应，可能包含```json ```标签
        json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
        if json_match:
            # 提取JSON部分
            json_content = json_match.group(1)
            try:
                result = json.loads(json_content)
            except json.JSONDecodeError:
                # 如果提取失败，尝试直接解析整个响应
                try:
                    result = json.loads(response_content)
                except json.JSONDecodeError:
                    logger.error("AI响应JSON解析失败")
                    return []
        else:
            # 没有```json ```标签，直接解析
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError:
                logger.error("AI响应JSON解析失败")
                return []
        
        # 解析新的JSON格式: {"attack_ips": [{"ip": "1.2.3.4", "attack_type": "DDoS"}, ...]}
        attack_data = result.get("attack_ips", [])
        
        # 记录攻击信息到数据库
        for attack in attack_data:
            ip = attack.get("ip")
            attack_type = attack.get("attack_type", "未知攻击")
            log_content = "\n".join(lines)  # 使用批次日志作为内容
            
            if ip:
                try:
                    # 记录攻击到数据库
                    db_manager.add_attack_record(
                        source_ip=ip,
                        attack_type=attack_type,
                        log_content=log_content,
                        severity=3,  # 默认中等严重程度
                        is_blocked=True  # 标记为需要封禁
                    )
                    logger.info(f"记录攻击: IP={ip}, 类型={attack_type}")
                except Exception as db_error:
                    logger.error(f"数据库记录失败: {db_error}")
        
        # 返回攻击信息字典格式
        attack_ips = [attack["ip"] for attack in attack_data if attack.get("ip")]
        attack_types = list(set([attack.get("attack_type", "未知攻击") for attack in attack_data]))
        
        return {
            "attack_ips": attack_ips,
            "attack_types": attack_types
        }
        
    except Exception as e:
        logger.error(f"调用 AI 接口失败: {e}")
        return []

# ================= 统计展示 =================
def show_attack_statistics():
    """显示攻击类型分组统计"""
    try:
        stats = db_manager.get_attack_type_summary()
        if stats:
            logger.info("=== 攻击类型统计 ===")
            total_attacks = sum(data["count"] for data in stats.values())
            for attack_type, data in stats.items():
                count = data["count"]
                avg_severity = data["avg_severity"]
                percentage = (count / total_attacks * 100) if total_attacks > 0 else 0
                logger.info(f"{attack_type}: {count} 次 ({percentage:.1f}%), 平均严重性: {avg_severity:.1f}")
            logger.info(f"总计: {total_attacks} 次攻击")
        else:
            logger.info("暂无攻击记录")
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")

# ================= 主循环 =================
def main():
    fw = FirewallAI()
    logger.info("开始监控日志，按 Ctrl+C 停止")
    
    # 初始化数据库连接
    try:
        # 测试数据库连接
        db_manager.get_attack_statistics()
        logger.info("数据库连接正常")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return
    
    # 统计展示计数器
    stat_counter = 0
    stat_interval = 10  # 每10次循环显示一次统计
    
    try:
        while True:
            batches = sample_log_lines()
            for batch in batches:
                if batch:  # 确保批次不为空
                    result = analyze_lines_ai(batch)
                    for ip in result["attack_ips"]:
                        fw.add_ip(ip)
            
            # 定期显示统计信息
            stat_counter += 1
            if stat_counter >= stat_interval:
                show_attack_statistics()
                stat_counter = 0
                
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("监控停止")
        # 退出前显示最终统计
        show_attack_statistics()

if __name__ == "__main__":
    main()
