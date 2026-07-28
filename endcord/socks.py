# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

import socket
import struct
from urllib.parse import urlparse


class Socks5UDPSocket:
    """socket.socket(AF_INET, SOCK_DGRAM) wrapper that adds SOCKS5 UDP proxy layer"""

    def __init__(self, proxy_url):
        self.proxy = urlparse(proxy_url)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_control = None
        self.relay_address = None
        self.target_address = None
        self.timeout = None


    def settimeout(self, value):
        """Set timeout for tcp and udp sockets"""
        self.timeout = value
        if self.tcp_control:
            self.tcp_control.settimeout(value)
        if self.udp_sock:
            self.udp_sock.settimeout(value)


    def connect(self, address):
        """Establish socks5 proxy handshake, authenticate, request udp associate relay, bind target address"""
        self.target_address = address   # (host, port)

        # init tcp control socket
        self.tcp_control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.timeout is not None:
            self.tcp_control.settimeout(self.timeout)
            self.udp_sock.settimeout(self.timeout)
        self.tcp_control.connect((self.proxy.hostname, self.proxy.port))

        # 2. socks5 auth
        if self.proxy.username and self.proxy.password:
            self.tcp_control.sendall(b"\x05\x02\x00\x02")   # client supports 'no auth' and 'user/pass auth'
            method_response = self.tcp_control.recv(2)
            if method_response == b"\x05\x02":   # user/pass auth
                username_b = self.proxy.username.encode("utf-8")
                password_b = self.proxy.password.encode("utf-8")
                auth_packet = b"\x01" + bytes([len(username_b)]) + username_b + bytes([len(password_b)]) + password_b
                self.tcp_control.sendall(auth_packet)
                if self.tcp_control.recv(2)[1] != 0x00:
                    raise RuntimeError("SOCKS5 Authentication failed: Invalid username or password")
            elif method_response != b"\x05\x00":
                raise RuntimeError("Proxy rejected supported authentication methods")
        else:   # no auth
            self.tcp_control.sendall(b"\x05\x01\x00")
            if self.tcp_control.recv(2) != b"\x05\x00":
                raise RuntimeError("Proxy requires authentication but none is provided")

        # request udp associate
        self.tcp_control.sendall(b"\x05\x03\x00\x01\x00\x00\x00\x00\x00\x00")
        reply = self.tcp_control.recv(1024)
        if reply[0] != 0x05 or reply[1] != 0x00:
            raise RuntimeError(f"SOCKS5 UDP associate request failed, error code: {reply[1]}")

        # read relay address
        atyp = reply[3]
        if atyp == 0x01:    # ipv4
            relay_ip = socket.inet_ntoa(reply[4:8])
            relay_port = struct.unpack("!H", reply[8:10])[0]
        elif atyp == 0x03:  # domain name
            domain_len = reply[4]
            relay_ip = reply[5:5+domain_len].decode()
            relay_port = struct.unpack("!H", reply[5+domain_len:7+domain_len])[0]
        else:
            raise NotImplementedError("IPv6 proxy relay targets are not handled in this implementation.")
        self.relay_address = (relay_ip, relay_port)


    def send(self, data):
        """Encapsulate payload into socks5 udp packet and send it to the relay"""
        host, port = self.target_address
        target_ip = socket.inet_aton(socket.gethostbyname(host))
        target_port = struct.pack("!H", port)
        # socks5 udp header = RSV(2) + FRAG(1) + ATYP(1) + IP(4) + PORT(2)
        header = b"\x00\x00\x00\x01" + target_ip + target_port
        self.udp_sock.sendto(header + data, self.relay_address)
        return len(data)


    def recv(self, bufsize):
        """Receive a packet from the relay and strip socks5 header"""
        if not self.udp_sock:
            raise RuntimeError("Socket is closed")
        packet, _ = self.udp_sock.recvfrom(bufsize + 32)
        if packet[3] == 0x01:
            return packet[10:]   # ipv4 header
        if packet[3] == 0x03:
            return packet[7 + packet[4]:]   # domain header
        return packet[22:]   # ipv6 header


    def close(self):
        """Close control connection and proxy udp socket"""
        if self.udp_sock:
            self.udp_sock.close()
        if self.tcp_control:
            self.tcp_control.close()


    def __enter__(self):   #noqa
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):   #noqa
        self.close()
