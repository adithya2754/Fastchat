import socket
import pickle
import psycopg2

HEADERSIZE = 10

conn = psycopg2.connect(
    database="fastchat",
    user="postgres",
    password="abhi@2707",
    host="127.0.0.1",
    port="7629",
)
cursor = conn.cursor()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 8867))
s.listen()

while True:
    Clientsocket, address = s.accept()
    cursor.execute("SELECT * FROM load_balance")
    servers = cursor.fetchall()
    conn.commit()
    min = 9999
    i = 0
    assigned_server = []
    for server in servers:
        if min > len(server[1]):
            min = len(server[1])
            assigned_server = server[0]
        i += 1
    if min >= 20:
        mssg = "None"
    elif min == -1:
        mssg = "No"
    else:
        mssg = assigned_server[0] + ", " + assigned_server[1]
    mssg = bytes(f"{len(mssg):<{HEADERSIZE}}", "utf-8") + mssg.encode("utf-8")
    Clientsocket.send(mssg)
    Clientsocket.close()