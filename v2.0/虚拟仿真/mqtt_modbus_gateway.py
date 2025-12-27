import json
import time
import threading
from pymodbus.client import ModbusTcpClient
import paho.mqtt.client as mqtt

# -------------------------- 配置参数 --------------------------
# Modbus 设备配置
MODBUS_DEVICE_IP = "127.0.0.1"  # Modbus设备IP（如果和网关同一机器则为127.0.0.1）
MODBUS_DEVICE_PORT = 502  # Modbus设备端口

# MQTT 服务器配置
MQTT_BROKER_IP = "182.92.0.11"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_STATUS = "ai4energy/blower_status"  # 状态上传话题
MQTT_TOPIC_CONTROL = "ai4energy/blower_control"  # 控制指令话题

# 采集间隔（秒）
COLLECT_INTERVAL = 5


# -------------------------- Modbus 操作函数 --------------------------
def modbus_read_fan_status():
    """读取风扇状态：启停（00003）和速度（40002）"""
    try:
        # 连接 Modbus 设备
        client = ModbusTcpClient(MODBUS_DEVICE_IP, port=MODBUS_DEVICE_PORT)
        client.connect()

        # 1. 读取线圈寄存器 00003（风扇启停）
        coil_response = client.read_coils(
            address=2, count=1, device_id=1
        )  # address=2 对应 00003
        is_run = coil_response.bits[0] if not coil_response.isError() else 0

        # 2. 读取保持寄存器 40002（风扇速度）
        holding_response = client.read_holding_registers(
            address=1, count=1, device_id=1
        )  # address=1 对应 40002
        run_speed = (
            holding_response.registers[0] if not holding_response.isError() else 1
        )

        # 关闭连接
        client.close()

        # 数据校验
        is_run = 1 if is_run else 0  # 确保是0/1
        run_speed = max(1, min(9, run_speed))  # 确保速度在1-9之间

        return {"is_run": is_run, "run_speed": run_speed}

    except Exception as e:
        print(f"Modbus 读取失败：{e}")
        return {"is_run": 0, "run_speed": 1}  # 默认值


def modbus_write_fan_control(is_run, run_speed):
    """写入风扇控制指令到 Modbus 设备"""
    try:
        # 连接 Modbus 设备
        client = ModbusTcpClient(MODBUS_DEVICE_IP, port=MODBUS_DEVICE_PORT)
        client.connect()

        # 数据校验
        is_run = 1 if is_run else 0  # 确保是0/1
        run_speed = max(1, min(9, run_speed))  # 确保速度在1-9之间

        # 1. 写入线圈寄存器 00003（风扇启停）
        client.write_coil(address=2, value=is_run, device_id=1)

        # 2. 写入保持寄存器 40002（风扇速度）
        client.write_register(address=1, value=run_speed, device_id=1)

        # 关闭连接
        client.close()

        print(f"Modbus 写入成功：is_run={is_run}, run_speed={run_speed}")
        return True

    except Exception as e:
        print(f"Modbus 写入失败：{e}")
        return False


# -------------------------- MQTT 操作函数 --------------------------
def on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    """MQTT 连接成功回调"""
    if reason_code == 0:
        print("MQTT 连接成功")
        # 订阅控制指令话题
        client.subscribe(MQTT_TOPIC_CONTROL)
    else:
        print(f"MQTT 连接失败，错误码：{reason_code}")


def on_mqtt_message(client, userdata, msg):
    """MQTT 消息接收回调（处理控制指令）"""
    try:
        # 解析消息
        payload = msg.payload.decode("utf-8")
        control_data = json.loads(payload)

        # 提取控制参数
        is_run = control_data.get("is_run", 0)
        run_speed = control_data.get("run_speed", 1)

        # 写入 Modbus 设备
        modbus_write_fan_control(is_run, run_speed)

    except json.JSONDecodeError:
        print("MQTT 消息格式错误：非合法JSON")
    except Exception as e:
        print(f"处理 MQTT 指令失败：{e}")


def mqtt_client_init():
    """初始化 MQTT 客户端"""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message

    # 连接 MQTT 服务器
    try:
        client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)
        return client
    except Exception as e:
        print(f"MQTT 客户端初始化失败：{e}")
        return None

# -------------------------- 网关主逻辑 --------------------------
def collect_and_upload_status(mqtt_client):
    """循环采集 Modbus 数据并上传到 MQTT"""
    while True:
        try:
            # 读取 Modbus 数据
            fan_status = modbus_read_fan_status()
            # 转换为 JSON 字符串
            payload = json.dumps(fan_status, ensure_ascii=False)
            # 发布到 MQTT
            mqtt_client.publish(MQTT_TOPIC_STATUS, payload, qos=1)
            print(f"上传状态到 MQTT：{payload}")
        except Exception as e:
            print(f"采集并上传状态失败：{e}")

        # 等待采集间隔
        time.sleep(COLLECT_INTERVAL)


if __name__ == "__main__":
    # 初始化 MQTT 客户端
    mqtt_client = mqtt_client_init()
    if not mqtt_client:
        exit(1)

    # 启动 MQTT 网络循环（后台线程）
    mqtt_client.loop_start()

    # 启动数据采集上传线程
    collect_thread = threading.Thread(
        target=collect_and_upload_status, args=(mqtt_client,)
    )
    collect_thread.daemon = True
    collect_thread.start()

    # 主线程保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("网关服务停止")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
