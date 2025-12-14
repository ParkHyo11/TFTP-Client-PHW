#!/usr/bin/python3
'''
$ tftp ip_address [-p port_mumber] <get|put> filename
'''
import socket
import argparse
from struct import pack
import os

# ===============================
# 기본 설정값 정의
# ===============================
DEFAULT_PORT = 69                 # TFTP 기본 포트
BLOCK_SIZE = 512                  # TFTP 데이터 블록 크기
DEFAULT_TRANSFER_MODE = 'octet'   # 바이너리 전송 모드

# ===============================
# TFTP 프로토콜 Opcode 정의
# ===============================
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}

MODE = {'netascii': 1,'octet': 2, 'mail': 3}

# ===============================
# TFTP 오류 코드 정의
# ===============================
ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

# ===============================
# WRQ (Write Request) 전송 함수
# ===============================
def send_wrq(filename, mode):
    # WRQ 패킷 포맷: opcode | filename | 0 | mode | 0
    format = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(
        format,
        OPCODE['WRQ'],
        bytes(filename, 'utf-8'),
        0,
        bytes(mode, 'utf-8'),
        0
    )
    # 서버로 WRQ 패킷 전송
    sock.sendto(wrq_message, server_address)
    print(wrq_message)

# ===============================
# RRQ (Read Request) 전송 함수
# ===============================
def send_rrq(filename, mode):
    # RRQ 패킷 포맷: opcode | filename | 0 | mode | 0
    format = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(
        format,
        OPCODE['RRQ'],
        bytes(filename, 'utf-8'),
        0,
        bytes(mode, 'utf-8'),
        0
    )
    # 서버로 RRQ 패킷 전송
    sock.sendto(rrq_message, server_address)
    print(rrq_message)

# ===============================
# ACK 전송 함수
# ===============================
def send_ack(seq_num, server):
    # ACK 패킷 포맷: opcode | block number
    format = f'>hh'
    ack_message = pack(format, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(seq_num)
    print(ack_message)

# ===============================
# PUT (파일 업로드) 기능
# ===============================
def put_file(filename):
    # 업로드할 로컬 파일 존재 여부 확인
    if not os.path.exists(filename):
        print("File not found.")
        return

    # 서버에 WRQ 전송
    send_wrq(filename, mode)

    try:
        # 서버로부터 ACK(0) 또는 ERROR 수신 대기
        data, server_new_socket = sock.recvfrom(516)
    except socket.timeout:
        print("No response to WRQ")
        return

    opcode = int.from_bytes(data[:2], 'big')

    # 서버에서 ERROR 응답을 보낸 경우
    if opcode == OPCODE['ERROR']:
        error_code = int.from_bytes(data[2:4], 'big')
        print(ERROR_CODE[error_code])
        return

    # ACK가 아니면 업로드 실패
    if opcode != OPCODE['ACK']:
        print("WRQ failed")
        return

    block_number = 1

    # 파일을 512바이트 단위로 읽어 DATA 전송
    with open(filename, 'rb') as file:
        while True:
            file_block = file.read(BLOCK_SIZE)

            data_format = f'>hh{len(file_block)}s'
            data_packet = pack(
                data_format,
                OPCODE['DATA'],
                block_number,
                file_block
            )

            # DATA 패킷 전송
            sock.sendto(data_packet, server_new_socket)

            # 서버로부터 ACK 수신
            ack_data, _ = sock.recvfrom(516)
            ack_opcode = int.from_bytes(ack_data[:2], 'big')
            ack_block = int.from_bytes(ack_data[2:4], 'big')

            # ACK 번호가 맞지 않으면 오류 처리
            if ack_opcode != OPCODE['ACK'] or ack_block != block_number:
                print("ACK error")
                return

            block_number += 1

            # 마지막 블록이면 전송 종료
            if len(file_block) < BLOCK_SIZE:
                break

# ===============================
# 명령행 인자 처리
# ===============================
parser = argparse.ArgumentParser(description='mytftp')
parser.add_argument(dest="host", help="Server IP address", type=str)
parser.add_argument(dest="operation", help="get or put a file", type=str)
parser.add_argument(dest="filename", help="name of file to transfer", type=str)
parser.add_argument("-p", "--port", dest="port", type=int)
args = parser.parse_args()

# ===============================
# 서버 정보 및 소켓 생성
# ===============================
server_ip = socket.gethostbyname(args.host)
server_port = args.port if args.port else DEFAULT_PORT
server_address = (server_ip, server_port)

# UDP 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)   # 응답 없을 경우 무한 대기 방지

mode = DEFAULT_TRANSFER_MODE
operation = args.operation
filename = args.filename

# ===============================
# GET (파일 다운로드) 기능
# ===============================
if operation == 'get':
    # RRQ 전송
    send_rrq(filename, mode)

    try:
        # 서버로부터 첫 DATA 수신
        data, server_new_socket = sock.recvfrom(516)
    except socket.timeout:
        print("No response to RRQ")
        exit(1)

    # 수신한 파일 저장을 위한 파일 생성
    file = open(filename, 'wb')
    expected_block_number = 1

    while True:
        opcode = int.from_bytes(data[:2], 'big')

        # DATA 패킷 처리
        if opcode == OPCODE['DATA']:
            block_number = int.from_bytes(data[2:4], 'big')

            # 기대한 블록 번호인 경우만 파일에 저장
            if block_number == expected_block_number:
                send_ack(block_number, server_new_socket)
                file_block = data[4:]
                file.write(file_block)
                expected_block_number += 1

                # 마지막 블록이면 종료
                if len(file_block) < BLOCK_SIZE:
                    file.close()
                    print(len(file_block))
                    break

                print(file_block.decode())
            else:
                # 중복 블록일 경우 ACK만 전송
                send_ack(block_number, server_new_socket)

        # ERROR 패킷 처리
        elif opcode == OPCODE['ERROR']:
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            break
        else:
            break

        # 다음 DATA 수신
        data, server_new_socket = sock.recvfrom(516)

# ===============================
# PUT 수행
# ===============================
elif operation == 'put':
    put_file(filename)

# ===============================
# 잘못된 명령 처리
# ===============================
else:
    print("use get or put")
