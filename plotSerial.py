#!/usr/bin/env python
# coding=utf-8

import serial
import time
import binascii
import threading
import signal
import ctypes
import xlwt

##### ------------------------------------------------------
# serial set
serial = serial.Serial()
serial.baudrate = 115200
serial.bytesize = 8
serial.parity = 'N'
serial.stopbits = 1
serial.timeout = 0.05   # rx timeout
##### ------------------------------------------------------
excel_file=xlwt.Workbook()
excel_table=excel_file.add_sheet("1")
excel_index=0
##### ------------------------------------------------------
# uart cmd type
CMD_ADV_SCAN = 0
CMD_ADV_SCAN_ACK = 1
CMD_CONNECT = 2
CMD_CONNECT_ACK = 3
CMD_DISCONN = 4
CMD_DISCONN_ACK = 5
CMD_READ_CH = 6
CMD_READ_CH_ACK = 7
CMD_WRITE_CH = 8
CMD_WRITE_CH_ACK = 9
CMD_NOTIFICATION = 10
CMD_DONGLE_STATE = 11
##### ------------------------------------------------------
# DG state
DG_IDEL = 0
DG_SCAN = 1
DG_CONNECTING = 2
DG_CONNECTED = 3
##### ------------------------------------------------------
## uart msg struct
## head data_len cmd data[] checksum
UART_MSG_HEAD = 0x55

##### ------------------------------------------------------
app_exit = False

wait_ack = False
wait_ack_type = CMD_ADV_SCAN_ACK
dg_connected = False
dg_cmd_state = 0

def signal_handler(signal, frame):
    global app_exit

    app_exit = True


def set_checksun(msg):
    len = msg[1]
    data = msg[3:]
    checksum = 0
    for i in data[0:len]:
        checksum ^= i
    msg.append(checksum)


def checksum(msg):
    len = msg[1]
    data = msg[3:]
    checksum = 0
    for i in data[0:len]:
        checksum ^= i
    
    if data[len] == checksum:
        return True
    else:
        return False


def snd_bytearray_uart(msg):
    global serial
    byte = serial.write(msg)
    serial.flush()
    return byte

def uart_msg_process(msg, msg_len):
        global wait_ack
        global wait_ack_type
        global dg_cmd_state
        global dg_connected
        global excel_table
        global excel_index

        data_len = msg[1]
        cmd = msg[2]
        data = msg[3:msg_len]

        if cmd == wait_ack_type:
            wait_ack = False
        print "\n\ruart_msg_process :",
        for byte in msg[0:msg_len]:
            print"%02X "%byte,
        print ""
        if cmd == CMD_ADV_SCAN_ACK:
            dg_cmd_state = data[0]
            print "- CMD_ADV_SCAN Rep :"
            if dg_cmd_state:
                print "- Mac :", 
                i = 6
                while i >= 1:
                    print "%02X:"%data[i],
                    i -= 1
                print "" 

                adv_len = data[7]
                rssi = data[7 + adv_len + 1]
                print "- advLen : %d"%adv_len
                i = 8
                print "- Data :", 
                while i < (adv_len + 8):
                    print "%02X"%data[i],
                    i += 1
                print "" 
                print "- Rssi %d"%ctypes.c_int8(rssi).value

            else:
                print "- Scan device adv timeout"

        elif cmd == CMD_CONNECT_ACK:
            dg_cmd_state = data[0]
            print "- CMD_CONNECT Rep :"
            if dg_cmd_state:
                print "- Connected with device :"
                print "- Mac :", 
                i = 6
                while i >= 1:
                    print "%02X:"%data[i],
                    i -= 1
                print "" 

                dg_connected = True
            else:
                print "- Sorry .. Connect device faile !!!" 

        elif cmd == CMD_DISCONN_ACK:
            print "- CMD_DISCONNECT Rep"
            dg_connected = True

        elif cmd == CMD_READ_CH_ACK:
            dg_cmd_state = data[0]
            print "- CMD_READ Rep :"
            if dg_cmd_state:
                read_len = data_len - 1 
                print "- len %d\ndata:"%(read_len),
                i = 1
                print "- Data :", 
                while i < (read_len + 1):
                    print "%02X"%data[i],
                    i += 1
                print "" 

            else:
                print "- read failed"

        elif cmd == CMD_WRITE_CH_ACK:
            dg_cmd_state = data[0]
            print "- CMD_WRITE Rep :"
            if dg_cmd_state:
                print "- write successful"
            else:
                print "- write failed"

        elif cmd == CMD_NOTIFICATION:
            print "- CMD_NOTIFICATION :"
            handle = data[0] | data[1] << 8
            read_len = data_len - 2 
            print "- handle 0X%04X len %d\ndata:"%(handle, read_len),
            i = 2
            print "- Data :", 
            while i < (read_len + 2):
                print "%02X"%data[i],
                i += 1
            print "" 
            excel_table.write(excel_index, 1, str(data[2:]))
            excel_index += 1

        elif cmd == CMD_DONGLE_STATE:
            print "- CMD_DONGLE_STATE :"
            state = data[0]
            dg_connected = False
            if state == DG_IDEL:
                print "- DG state DG_IDEL" 
            elif state == DG_SCAN:
                print "- DG state DG_SCAN" 
            elif state == DG_CONNECTING:
                print "- DG state DG_CONNECTING" 
            elif state == DG_CONNECTED:
                print "- DG state DG_CONNECTED" 
                dg_connected = True
            else :
                print "- DG state error , reboot it may a goog way" 
        else:
            print("- uart_msg_process : unknow cmd")


class read_thread(threading.Thread):

    def __init__(self, serial):
        threading.Thread.__init__(self)
        self.serial = serial
        self.quit = False

    def run(self):

        rx_fifo = []
        rx_status = 0
        rx_msg_len = 0
        while not self.quit:

            byte  = self.serial.read(1)
            if byte != '':
                byte = binascii.b2a_hex(byte) 
                rx_fifo.append(int(byte, 16))

            if len(rx_fifo) > 3:
                # get header
                if rx_status == 0 :
                    while len(rx_fifo) > 0 and rx_fifo[0] != UART_MSG_HEAD:
                        del rx_fifo[0]
                    if len(rx_fifo) > 0:
                        rx_status = 1
                #get len
                if rx_status == 1:
                    if len(rx_fifo) > 1:
                        rx_msg_len = rx_fifo[1] + 4
                        rx_status = 2
                #get total msg
                if rx_status == 2 and len(rx_fifo) >= rx_msg_len:
                    if checksum(rx_fifo):
                        # handle msg
                        uart_msg_process(rx_fifo, rx_msg_len)
                        del rx_fifo[0:rx_msg_len]
                    else:
                        del rx_fifo[0]

                    rx_status = 0


def wait_dg_ack(type, timeout=10):
    
    global wait_ack
    global wait_ack_type
    timeout *= 10
    wait_ack = True
    wait_ack_type = type

    while wait_ack and timeout:
        time.sleep(0.1)
        timeout -= 1
    if timeout:
        return True
    else:
        print "\nwait timeout\n"
        return False


def dg_scan_ble(mac, timeout=10):
    global dg_cmd_state

    dg_cmd_state = 0
    adv_scan = [UART_MSG_HEAD, 7, CMD_ADV_SCAN]
    i = len(mac)
    while i > 0:
        adv_scan.append(int(mac[(i-2):i], 16))
        i -= 2
    adv_scan.append(timeout)
    set_checksun(adv_scan)

    sndmsg = bytearray(adv_scan)
    snd_bytearray_uart(sndmsg)
    wait_dg_ack(CMD_ADV_SCAN_ACK, timeout + 2)
    return dg_cmd_state


def dg_connect_device(mac, timeout=10):
    global dg_cmd_state

    dg_cmd_state = 0
    conn = [UART_MSG_HEAD, 7, CMD_CONNECT]
    i = len(mac)
    while i > 0:
        conn.append(int(mac[(i-2):i], 16))
        i -= 2
    conn.append(timeout)
    set_checksun(conn)

    sndmsg = bytearray(conn)
    snd_bytearray_uart(sndmsg)
    wait_dg_ack(CMD_CONNECT_ACK, timeout + 2)
    return dg_cmd_state


def dg_disconnect_device():
    conn = [UART_MSG_HEAD, 0, CMD_DISCONN]
    set_checksun(conn)
    sndmsg = bytearray(conn)
    snd_bytearray_uart(sndmsg)
    return wait_dg_ack(CMD_DISCONN_ACK, 5)


def dg_read_ble(handle):
    msg = [UART_MSG_HEAD, 2, CMD_READ_CH]
    msg.append(handle&0xFF)
    msg.append(handle>>8)
    set_checksun(msg)
    sndmsg = bytearray(msg)
    snd_bytearray_uart(sndmsg)
    return wait_dg_ack(CMD_READ_CH_ACK, 5)


def dg_write_ble(handle, data, respone=True):
    write = [UART_MSG_HEAD, 0, CMD_WRITE_CH]

    write_len = len(data)

    if respone:
        write.append(0x01)
    else:
        write.append(0x00)

    write.append(handle&0xFF)
    write.append(handle>>8)
    i = 0
    while i < write_len:
        write.append(data[i])
        i += 1
    write[1] = 3 + write_len # data len
    set_checksun(write)
    sndmsg = bytearray(write)
    snd_bytearray_uart(sndmsg)
    return wait_dg_ack(CMD_WRITE_CH_ACK, 5)


if __name__ == "__main__":

    serial.port = "/dev/ttyUSB2"
    mac = "229900000003"

    serial.open()
    if serial.isOpen():
        try:
            signal.signal(signal.SIGINT, signal_handler)

            readThread = read_thread(serial)
            readThread.start()
            while not app_exit:

                #data = "220302010001"
                #sndmsg = binascii.a2b_hex(data)
                # let dg scan adv

                if dg_scan_ble(mac):
                    if dg_connect_device(mac):

                        # set listening , value's handler + 1 write [0x01 0x00]
                        if dg_write_ble(0x0023 + 1, [0x01, 0x00]):
                        #dg_write_ble(0x0034 + 1, [0x01, 0x00])

                            time.sleep(2)
                            data = [0x22, 0x04, 0x02, 0x0b, 0x01, 0x04, 0x00]
                            dg_write_ble(0x0023, data) # write with respone
                            time.sleep(1)
                            dg_disconnect_device()
                            dg_connect_device(mac)

                        dg_disconnect_device()
                        time.sleep(1)

                #app_exit = True
        except:
            pass

        finally :
            serial.flushInput()
            serial.flushOutput()
            readThread.quit = True
            readThread.join()
            readThread = None
            serial.close()
            excel_table.write(excel_index, 1, "done")
            save_time=time.strftime('%Y-%m-%d_%H:%M:%S',time.localtime(time.time()))
            excel_file.save(str(save_time) + '.xls')
            print "App quit"

    else:
        print("Serial open error")

