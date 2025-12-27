
import sys
from pymodbus.client import ModbusTcpClient

# -------------------------- 配置参数 --------------------------
# Modbus 设备配置
MODBUS_DEVICE_IP = "192.168.3.120"  # Modbus设备IP
MODBUS_DEVICE_PORT = 502        # Modbus设备端口

# -------------------------- Modbus 控制函数 --------------------------
def modbus_write_fan_control(is_run, run_speed):
    """
    直接写入风扇控制指令到 Modbus 设备
    
    参数:
        is_run (int): 风扇启停状态 (0=停止, 1=启动)
        run_speed (int): 风扇速度 (1-9级)
    """
    try:
        # 连接 Modbus 设备
        client = ModbusTcpClient(MODBUS_DEVICE_IP, port=MODBUS_DEVICE_PORT)
        if not client.connect():
            print("无法连接到 Modbus 设备")
            return False

        # 数据校验
        is_run = 1 if is_run else 0  # 确保是0/1
        run_speed = max(1, min(9, run_speed))  # 确保速度在1-9之间

        # 1. 写入线圈寄存器 00003（风扇启停）
        coil_result = client.write_coil(address=2, value=is_run, device_id=1)
        if coil_result.isError():
            print("写入线圈寄存器失败")
            client.close()
            return False

        # 2. 写入保持寄存器 40002（风扇速度）
        register_result = client.write_register(address=1, value=run_speed, device_id=1)
        if register_result.isError():
            print("写入保持寄存器失败")
            client.close()
            return False

        # 关闭连接
        client.close()

        print(f"Modbus 指令下发成功：is_run={is_run}, run_speed={run_speed}")
        return True

    except Exception as e:
        print(f"Modbus 指令下发失败：{e}")
        return False

# -------------------------- 主程序 --------------------------
def main():
    """主函数 - 处理命令行参数并执行控制指令"""
    
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: python modbus_control.py <is_run> <run_speed>")
        print("示例: python modbus_control.py 1 5")
        print("      is_run: 0(停止) 或 1(启动)")
        print("      run_speed: 1-9 (速度等级)")
        return 1
    
    try:
        # 解析命令行参数
        is_run = int(sys.argv[1])
        run_speed = int(sys.argv[2])
        
        # 参数验证
        if is_run not in [0, 1]:
            print("错误: is_run 必须是 0 或 1")
            return 1
            
        if run_speed < 1 or run_speed > 9:
            print("错误: run_speed 必须在 1-9 之间")
            return 1
        
        # 执行控制指令
        success = modbus_write_fan_control(is_run, run_speed)
        return 0 if success else 1
        
    except ValueError:
        print("错误: 参数必须是整数")
        return 1
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())