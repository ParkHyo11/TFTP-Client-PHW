본 프로젝트는 UDP를 기반으로한 TFTP 클리언트를 파이썬으로 구현한 과제용 프로그램입니다.
파일을 가져와 다운로드하는 get과 업로드하는 put 기능을 제공합니다.
전송모드는 octec 모드만 지원하며, 호스트 주소는 도메인네임과 IP 주소로 지정합니다.
RRQ와 WRQ에 서버가 응답이 없을 경우 응답 없음 처리를 하였으며, File not found와 File arleady exists 오류를 처리하였습니다.

##개발 환경:
OS: Linux
언어: 파이썬
네트워크: UDP 소켓
프로토콜: TFTP

##클라이언트 실행:
./TFTPClient.py host [-p port] [get|put] filename

##주요 기능
1. GET (파일 다운로드):
RRQ 패킷을 전송
서버로부터 DATA 블록을 수신
블록 번호 확인 후 ACK 전송
마지막 블록 수신 시 종료

2. PUT (파일 업로드):
WRQ 패킷을 전송
서버에 ACK(0) 수신 후 DATA 블록을 전송
각 DATA 전송 후 ACK 확인

##포트 옵션 (-p):
기본적으로 TFTP 표준 포트(69)를 사용
-p 옵션을 통해 서버 포트 번호 지정 가능

##오류 처리:
서버로부터 ERROR 패킷 수신 시 오류 코드 출력
