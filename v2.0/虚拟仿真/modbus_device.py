from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext

class LoggingDataBlock(ModbusSequentialDataBlock):
    """带日志功能的数据块"""
    
    def __init__(self, address, values, name=""):
        super().__init__(address, values)
        self.name = name
        
    def setValues(self, address, values):
        """重写setValues方法以添加日志"""
        old_values = [self.getValues(a, 1)[0] for a in range(address, address + len(values))]
        result = super().setValues(address, values)
        print(f"[{self.name}] 数据变更: 地址 {address} 从 {old_values} 更改为 {values}")
        return result

# 初始化寄存器数据
# 线圈寄存器（00001-00009）：00003 对应索引 2（从0开始），初始值 0（停止）
coil_block = LoggingDataBlock(0, [0]*10, "线圈寄存器")
coil_block.setValues(2, [0])  # 00003 = 0

# 保持寄存器（40001-40009）：40002 对应索引 1（从0开始），初始值 1（最低速度）
holding_block = LoggingDataBlock(0, [0]*10, "保持寄存器")
holding_block.setValues(1, [1])  # 40002 = 1

# 创建从站上下文
device_context = ModbusDeviceContext(
    co=coil_block,      # 线圈寄存器（读写）
    hr=holding_block,   # 保持寄存器（读写）
)

# 创建服务器上下文
server_context = ModbusServerContext(devices=device_context, single=True)

if __name__ == "__main__":
    # 启动 Modbus TCP 服务器，监听 502 端口（标准Modbus端口）
    print("Modbus TCP 模拟设备启动，监听 0.0.0.0:502")
    print("寄存器地址映射:")
    print("  线圈寄存器: 00003 (索引2) - 风扇启停状态")
    print("  保持寄存器: 40002 (索引1) - 风扇速度")
    StartTcpServer(
        context=server_context,
        address=("0.0.0.0", 502)
    )