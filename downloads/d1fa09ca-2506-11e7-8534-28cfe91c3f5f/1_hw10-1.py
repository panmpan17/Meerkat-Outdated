import socket

address = ('<broadcast>', 54545)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

data = "Request"
client_socket.sendto(data.encode(), address)

recv_data, addr = client_socket.recvfrom(2014)
print(addr)