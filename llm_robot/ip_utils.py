import socket

def get_ip_addresses():
    ip_list = []
    import socket
    try:
        for iface in socket.if_nameindex():
            iface_name = iface[1]
            try:
                import fcntl, struct
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ip = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', iface_name[:15].encode('utf-8'))
                )[20:24])
                if ip not in ip_list and not ip.startswith('127.'):
                    ip_list.append(ip)
            except:
                continue
    except:
        pass
    # 로컬호스트 추가
    ip_list.append('127.0.0.1')
    return ip_list
