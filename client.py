# Written by Geoffrey Stentiford
# This file has zero LLM output in it

import sys
import multiprocessing
from multiprocessing.sharedctypes import SynchronizedArray, Synchronized
from typing import Tuple, List

SOCKET = "/tmp/ac_bridge"

standalone: bool = False
dVals: SynchronizedArray = multiprocessing.Array('d', 5)
rVals: SynchronizedArray = multiprocessing.Array('d', 5)
mode: Synchronized = multiprocessing.Value('i')
time:  SynchronizedArray = multiprocessing.Array('d', 2)
state: SynchronizedArray = multiprocessing.Array('i', 3)

state[0] = 0 # connection down
state[1] = 1 # spin

rogue: List[Tuple[float, float]] = list()
disco: List[Tuple[float, float]] = list()
time[0] = 0.0
time[1] = 0.0

def internal_runner(dVals: SynchronizedArray, rVals: SynchronizedArray, mode: Synchronized, state: SynchronizedArray, time: Synchronized, path: str):
    import socket
    import json

    try:
        def conn_kill(conx: socket.socket):
            conx.shutdown(socket.SHUT_RDWR)
            conx.close()

        state[0] = 0 # connection down
        state[1] = 1 # module busys

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(path)
        client.sendall("0".encode())
        print(f"Connected on {path}")
        
        state[0] = 1 # connection up

        try:
            while state[1] == 1: # while spinning
                connection = client.accept()[0]
                data = connection.recv(1024)
                msg: Tuple[List[float], List[float], float, int] = tuple(json.loads(data))
                time[1] = time[0]
                for i in range(5):
                    dVals[i] = msg[0][i]
                    rVals[i] = msg[1][i]
                time[0] = float(msg[2])
                mode.value = int(msg[3])
        except InterruptedError:
            print("IPC UNIX socket connection closed")
            conn_kill(connection)
        except KeyboardInterrupt:
            print("Exiting")
            conn_kill(connection)
    finally:
        sys.exit(0)

def getVals():
    if time[0] != time[1]:
        disco.append((dVals[0], dVals[1]))
        if rVals[0] != 0.0:
            rogue.append((rVals[0], rVals[1]))
    return disco, rogue

# def getVals():
#     return (dVals[0], dVals[1]), (rVals[0], rVals[1])

def getMode() -> int:
    return mode.value

def getTimestamp():
    return float(time[0])

def isConnected():
    return True if state[0] == 1 else False

def unix_handler(sig, frame):
    state[1] = 0 # stop
    state[0] = 0 # connection down
    p1.terminate()
    try:
        p1.kill()
    finally:
        p1.join()
        p1.close()
    sys.exit(0)

def start():
    import signal
    global p1
    
    p1 = multiprocessing.Process(None, internal_runner, None, (dVals, rVals, mode, state, time, SOCKET), daemon=True)

    signal.signal(signal.SIGINT, unix_handler)
        
    p1.start()