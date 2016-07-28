## 20160725
### 蓝牙dongle开发
#### 功能
1. 广播搜索
2. 设备连接/断开
3. 读设备特征值
4. 写设备特征值

---

#### 串口通信规定

**数据格式：**
| Head | Len | Type | ``Data`` | Checksum |
|:----:|:---:|:----:|:----:|:--------:|
| 0X55 | Data's len | xx | xxxxx | Data^ |

**Type 类型 :**
```c
enum {
    ADV_SCAN，
    ADV_SCAN_ACK，
    CONNECT，
    CONNECT_ACK，
    DISCONN，
    DISCONN_ACK, 
    READ_CH,
    READ_CH_ACK, 
    WRITE_CH,
    WRITE_CH_ACK,
    NOTIFICATION,
    DONGLE_STATE,
} uartCmdType;

enum {
	DG_IDEL,
	DG_SCAN,
	DG_CONNECTING,
	DG_CONNECTED,
} dongleState;


```
**Type 及其对应数据段格式 :**
1 广播搜索
```
* 发起广播搜索
Data : Mac(6byte : L -> H) + Timeout(1byte : s)
* 扫描到指定设备应答
Data : 1 +  Mac(6byte : L -> H) + advlen + advdata[] + rssi
* 超时应答
Data : 0
```
2 设备连接
```
* 发起连接
Data : Mac(6byte : L -> H) + Timeout(1byte : s)
* 连接到指定设备应答
Data : 1 +  Mac(6byte : L -> H)
* 超时应答
Data : 0
```
3 断开连接
```
* 断开连接
Data : 
* 应答 
Data : 
```
4 读设备
```
* 发送命令
Data : handle(2byte)
* 返回应答
Data : 1 + data[]
* 错误应答
Data ： 0
```
5 写设备
```
* 发送命令
Data : 1(0免应答) + handle(2byte) + write[] 
* 返回应答
Data : 1
* 错误应答
Data : 0
```
6 收到设备notif
```
Data : handle(2byte) + data[]
```
7 dongle 当前状态
```
Data : dongle_state(1byte)
```
**说明**
1. 不同命令包按照类型指定格式填充``Data``段， 通过串口传递。
2. 采用20736模块串口通信单包长度 ： 15 byte。
3. 小端格式