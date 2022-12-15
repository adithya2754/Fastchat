import socket
import psycopg2, pickle, select

HEADERSIZE = 10
HEADER_LENGTH = 10

conn = psycopg2.connect(
    database="fastchat",
    user="postgres",
    password="sandy@08",
    host="127.0.0.1",
    port="5432",
)
cursor = conn.cursor()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((socket.gethostname(), 9999))
server_socket.listen()
sockets_list = [server_socket]
clients = {}


def recieveMessage(client_socket):
    """This function recieves messages from servers
    
    :param client_socket: socket of a server that is connected to master_server
    :type client_socket: socket
    :return: message from the server
    :rtype: dictionary
    """
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        # if message_header is null
        if not len(message_header):
            return False

        message_length = int(message_header.decode("utf-8").strip())
        return {
            "header": message_header,
            "data": client_socket.recv(message_length),
        }

    except:
        return False


while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for socket in read_sockets:
        if socket == server_socket:
            client_socket, client_address = server_socket.accept()
            user = recieveMessage(client_socket)

            # if socket got disconnected:
            if user is False:
                continue

            # online sockets appending the current socket
            sockets_list.append(client_socket)

            clients[client_socket] = user

            print(
                f"Accepted a new connection from {client_address[0]}:{client_address[1]}. username : {user['data'].decode('utf-8')}"
            )

        else:
            message_recieved = recieveMessage(socket)

            if message_recieved is False:
                print(
                    f"Closed connection from server with ip, port : {clients[socket]['data'].decode('utf-8')}"
                )
                cursor.execute(
                    "DELETE FROM load_balance WHERE server=ARRAY[%s,%s]",
                    (
                        str(clients[socket]["data"].decode("utf-8").split(", ")[0]),
                        str(clients[socket]["data"].decode("utf-8").split(", ")[1]),
                    ),
                )
                conn.commit()
                sockets_list.remove(socket)
                del clients[socket]
                continue

            user = clients[socket]
            print(
                f"Recieved data from {user['data'].decode('utf-8')}: {message_recieved['data'].decode('utf-8')}"
            )

            message = recieveMessage(socket)
            TO = pickle.loads(message["data"])[1]
            SERVERS = []
            for i in clients.values():
                SERVERS.append(
                    (
                        i["data"].decode("utf-8").split(", ")[0],
                        i["data"].decode("utf-8").split(", ")[1],
                    )
                )
            print(SERVERS)

            cursor.execute("SELECT * FROM load_balance")
            res = cursor.fetchall()
            conn.commit()
            Ser = []
            for row in res:
                for client in row[1]:
                    if client == TO:
                        Ser = row[0]
                        break
            if Ser == []:
                continue
            print(Ser)
            Ser = Ser[0] + ", " + Ser[1]
            for client_socket in clients:
                if clients[client_socket]["data"].decode("utf-8") == Ser:
                    client_socket.send(
                        message_recieved["header"]
                        + message_recieved["data"]
                        + message["header"]
                        + message["data"]
                    )

    for socket in exception_sockets:
        sockets_list.remove(socket)
        del clients[socket]