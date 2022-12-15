import socket
import select
import pickle
import psycopg2
import bcrypt
from datetime import datetime
from simplecrypt import encrypt, decrypt
import sys
import re

conn = psycopg2.connect(
    database="fastchat",
    user="postgres",
    password="abhi@2707",
    host="127.0.0.1",
    port="7629",
)
cursor = conn.cursor()

HEADERLENGTH = 10
IP = socket.gethostbyname(socket.gethostname())
PORT = 7777

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
group_list = [server_socket]

clients = {}
GROUP = []



cursor.execute("SELECT username,status FROM user_info")
CLIENTS = cursor.fetchall()
conn.commit()
cursor.execute("SELECT * FROM groups_info")
GROUPS = cursor.fetchall()
conn.commit()

def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADERLENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode("utf-8").strip())
        return {"header": message_header, "data": client_socket.recv(message_length)}

    except:
        return False


cursor.execute("UPDATE user_info SET status =%s RETURNING *", ("offline",))
conn.commit()


while True:
    read_sockets, not_req, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            user = receive_message(client_socket)

            if user is False:
                continue

            sockets_list.append(client_socket)  # DB adding the client data into the list
            doin = pickle.loads(user["data"])[0]
            if doin == "LOGIN":
                username = pickle.loads(user["data"])[1]
                password = pickle.loads(user["data"])[2]
                cursor.execute(
                    "SELECT * FROM user_info WHERE username =%s AND password =%s",
                    (
                        username,
                        bcrypt.hashpw(
                            password.encode("utf-8"),
                            b"$2b$12$hwqJlFqHRP659BwR5VnUz.",
                        ).decode(),
                    ),
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    mms = "Incorrect username or password"
                else:
                    cursor.execute(
                        "UPDATE user_info SET status=%s WHERE username = %s",
                        ("online", username),
                    )
                    conn.commit()
                    mms = "Welcome back to fastchat...!"

            elif doin == "SIGNUP":
                username = pickle.loads(user["data"])[1]
                password = pickle.loads(user["data"])[2]
                public_key = pickle.loads(user["data"])[3]
                cursor.execute(
                    "SELECT * FROM user_info WHERE username =%s", (username,)
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    bytes2 = password.encode("utf-8")
                    salt = b"$2b$12$hwqJlFqHRP659BwR5VnUz."
                    hash = bcrypt.hashpw(bytes2, salt)
                    status = "online"
                    cursor.execute(
                        """INSERT INTO user_info(username, password, status, public_key)
                        VALUES(%s, %s, %s, %s)
                        """,
                        (username, hash.decode(), status, pickle.dumps(public_key)),
                    )
                    conn.commit()
                    CLIENTS.append(username)
                    mms = "Welcome to fastchat...!"
                else:
                    mms = "Username is already in use"
            clients[client_socket] = user
            if (
                mms == "Welcome to fastchat...!"
                or mms == "Welcome back to fastchat...!"
            ):
                serv = "SERVER"
                serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                mms = (mms, "ryt-data")
                mms = pickle.dumps(mms)
                mms_he = bytes(f"{len(mms) :<{HEADERLENGTH}}", "utf-8")
                client_socket.send(
                    serv_he + serv.encode("utf-8") + mms_he + mms
                )
                print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username:{pickle.loads(user['data'])[1]}")
            else:
                serv = "SERVER"
                serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                mms = (mms, "wrg-data")
                mms = pickle.dumps(mms)
                mms_he = bytes(f"{len(mms) :<{HEADERLENGTH}}", "utf-8")
                client_socket.send(serv_he + serv.encode("utf-8") + mms_he + mms)
                # sockets_list.remove(client_socket)
                # del clients[client_socket]
                # client_socket.close()

        else:
            message = receive_message(notified_socket)

            if message is False:
                print(
                    f"Closed connection from {pickle.loads(clients[notified_socket]['data'])[1]}"
                )
                cursor.execute(
                    "UPDATE user_info SET status=%s WHERE username = %s",
                    ("offline", pickle.loads(clients[notified_socket]["data"])[1]),
                )
                conn.commit()
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            user = clients[notified_socket]
            message_con = pickle.loads(message["data"])[0]
            message_to = pickle.loads(message["data"])[1]

            if message_to == "SERVER":
                if message_con == "list of chats":
                    ms = "Here is the list of your chats\n" + "Personal chats:\n"
                    i = 0
                    for client_socket in clients:
                        if (
                            pickle.loads(clients[client_socket]["data"])[1]
                            != pickle.loads(user["data"])[1]
                        ):
                            sel = "SERVER"
                            sel_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                            ms = (
                                ms
                                + "   "
                                + pickle.loads(clients[client_socket]["data"])[1]
                                + "\n"
                            )
                            i += 1
                    if i == 0:
                        ms = ms + "    You have no personal chats\n"
                    ms = ms + "group chats:\n"
                    i = 0
                    for grp in GROUP:
                        if list(grp.values()).count(pickle.loads(user["data"])[1]):
                            ms = ms + "   " + grp["GROUP_NAME"] + "\n"
                            i += 1
                    if i == 0:
                        ms = ms + "    You have no group chats\n"

                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
 
            elif (message_to == "PPUBLIC-KEY"):
                cursor.execute("SELECT * FROM user_info WHERE username = %s", (str(message_con),))
                public_keys = cursor.fetchall()
                conn.commit()
                key = pickle.loads(public_keys[0][3])
                ks = (key, "key-data")
                ks = pickle.dumps(ks)
                serv = "SERVER"
                serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", 'utf-8')
                ks_he = bytes(f"{len(ks) :<{HEADERLENGTH}}", 'utf-8')
                notified_socket.send(serv_he + serv.encode('utf-8') + ks_he + ks)
                    
            elif (message_to == "GPUBLIC-KEY"):
                cursor.execute("SELECT * FROM groups_info WHERE group_name = %s", (str(message_con),))
                gpublic_keys = cursor.fetchall()
                conn.commit()
                gkey = gpublic_keys[0][2]
                gpkeys = []
                for ptc in gkey:
                    cursor.execute("SELECT * FROM user_info WHERE username = %s", (str(ptc),))
                    ggg = cursor.fetchall()
                    conn.commit()
                    gpkeys.append((ggg[0][0], pickle.loads(ggg[0][3])))
                    pass
                gks = (gpkeys, "gkey-data")
                gks = pickle.dumps(gks)
                serv = "SERVER"
                serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", 'utf-8')
                gks_he = bytes(f"{len(gks) :<{HEADERLENGTH}}", 'utf-8')
                notified_socket.send(serv_he + serv.encode('utf-8') + gks_he + gks)
                pass
            
            elif ( message_to !="SERVER"
                and message_to != "GROUP"
                and message_to != "GROUP_MESSAGE"
                and message_to != "gManipl"
                and message_to != "apowadd"
                and message_to != "apowrem"
                and message_to != "UNREAD-MSSG"
            ):
                print(
                    f"Received message from {pickle.loads(user['data'])[1]} to {message_to}"
                )
                cursor.execute(
                    "SELECT * FROM user_info WHERE username = %s", (str(message_to),)
                )
                To = cursor.fetchall()
                conn.commit()
                if To[0][2] == "offline":
                    cursor.execute(
                        """INSERT INTO unreadMessages(from_person, to_person, type_of_message, Message, PostedAt)
                                   VALUES(%s,%s,%s,%s,%s)""",
                        (
                            pickle.loads(user["data"])[1],
                            message_to,
                            message_con[0],
                            pickle.dumps(message_con[1]),
                            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        ),
                    )
                    conn.commit()
                else:
                    for client_socket in clients:
                        if (
                            pickle.loads(clients[client_socket]["data"])[1]
                            == message_to
                        ):
                            se = bytes(
                                f"{len(pickle.loads(user['data'])[1]) :<{HEADERLENGTH}}",
                                "utf-8",
                            )
                            if message_con[0] == "text":
                                client_socket.send(
                                    se
                                    + pickle.loads(user["data"])[1].encode("utf-8")
                                    + message["header"]
                                    + pickle.dumps(message_con)
                                )
                            elif message_con[0] == "image":
                                cursor.execute(
                                    "INSERT INTO media(from_person, to_person, image) VALUES(%s, %s, %s)",
                                    (
                                        pickle.loads(user["data"])[1],
                                        message_to,
                                        message_con[1],
                                    ),
                                )
                                conn.commit()
                                client_socket.send(
                                    bytes( f"{len(pickle.loads(user['data'])[1])+1 :<{HEADERLENGTH}}","utf-8",)
                                    + (pickle.loads(user["data"])[1] + ",").encode("utf-8")
                                    + message["header"]
                                    + pickle.dumps(message_con)
                                )

            elif message_to == "GROUP":
                print(
                    f"GROUP {message_con['GROUP_NAME']} created by {message_con['Admin']}"
                )
                l = []
                for part in message_con:
                    if (
                        part != "GROUP_NAME"
                        or part != "Admin"
                    ):
                        print(f"{part}: {message_con[part]}")
                        l.append(message_con[part])

                cursor.execute(
                    "SELECT * FROM groups_info WHERE group_name =%s",
                    (message_con["GROUP_NAME"],),
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) != 0:
                    # print("A group with this name already exists")
                    ms = "A group with this name already exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                    continue
                cursor.execute(
                    """INSERT INTO groups_info(group_name, admin_name, group_participants)
                            VALUES(%s, %s, ARRAY[%s])
                            """,
                    (
                        message_con["GROUP_NAME"],
                        message_con["Admin"],
                        message_con["Admin"],
                    ),
                )
                conn.commit()
                # l = l[2:]
                for par_name in l:
                    cursor.execute(
                        "SELECT * FROM user_info WHERE username =%s", (par_name,)
                    )
                    res1 = cursor.fetchall()
                    conn.commit()
                    if len(res1) == 0:
                        ms = f"Participant with name {par_name} not exists"
                        ms = (ms, "auth-data")
                        ms = pickle.dumps(ms)
                        serv = "SERVER"
                        serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                        ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                        notified_socket.send(
                            serv_he + serv.encode("utf-8") + ms_he + ms
                        )
                        continue
                    cursor.execute(
                        "SELECT * FROM groups_info WHERE group_name =%s",
                        (message_con["GROUP_NAME"],),
                    )
                    res = cursor.fetchall()
                    conn.commit()
                    # if(res[0][1]!=message_con['Admin']):
                    #     print("Only admin can add partipants")
                    check = 0
                    for i in res[0][2]:
                        if i == par_name:
                            check = 1
                            ms = f"Participant with name {par_name} already exits in group"
                            ms = (ms, "auth-data")
                            ms = pickle.dumps(ms)
                            serv = "SERVER"
                            serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                            ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                            notified_socket.send(
                                serv_he
                                + serv.encode("utf-8")
                                + ms_he
                                + ms
                            )
                    if check:
                        continue
                    cursor.execute(
                        "UPDATE groups_info SET group_participants = array_append(group_participants, %s) WHERE group_name = %s",
                        (
                            par_name,
                            message_con["GROUP_NAME"],
                        ),
                    )
                    conn.commit()

                GROUP.append(message_con)
                for client_socket in clients:
                    if list(message_con.values()).count(
                        pickle.loads(clients[client_socket]["data"])[1]
                    ):
                        if (
                            pickle.loads(clients[client_socket]["data"])[1]
                            != message_con["Admin"]
                        ):
                            stri = f"you were added to the group {message_con['GROUP_NAME']} by {message_con['Admin']}"
                            stri = (stri, "auth-data")
                            stri = pickle.dumps(stri)
                            serv = "SERVER"
                            serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                            client_socket.send(
                                serv_he
                                + serv.encode("utf-8")
                                + message["header"]
                                + stri
                            )

            elif message_to == "gManipl":
                a = "00"
                cursor.execute(
                    "SELECT * FROM groups_info WHERE group_name =%s", (message_con,)
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    ms = "Group with this name doesnot exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                    a = "10"
                elif res[0][1] != pickle.loads(user["data"])[1]:
                    ms = "Only admin can add partipants"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                    a = "10"
                else:
                    a = "11"
                a = (a, "adm-data")
                a = pickle.dumps(a)
                a_he = bytes(f"{len(a) :<{HEADERLENGTH}}", "utf-8")
                serv = "SERVER"
                serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                notified_socket.send(
                    serv_he + serv.encode("utf-8") + a_he + a
                )

            elif message_to == "apowadd":
                check1 = 1
                cursor.execute(
                    "SELECT * FROM user_info WHERE username =%s", (message_con[0],)
                )
                res1 = cursor.fetchall()
                conn.commit()
                if len(res1) == 0:
                    print(f"Participant with name {message_con[0]} not exists")
                    ms = "Participant with that name not exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                    check1 = 0
                cursor.execute(
                    "SELECT * FROM groups_info WHERE group_name =%s",
                    (message_con[1],),
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    # ms = f"Group with name {message_con[1]} does not exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                for i in res[0][2][2:]:
                    if i == message_con[0]:
                        ms = f"Participant with name {message_con[0]} already exits in group"
                        ms = (ms, "auth-data")
                        ms = pickle.dumps(ms)
                        serv = "SERVER"
                        serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                        ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                        notified_socket.send(
                            serv_he + serv.encode("utf-8") + ms_he + ms
                        )
                        check1 = 0
                if check1 == 1:
                    cursor.execute(
                        "UPDATE groups_info SET group_participants = array_append(group_participants, %s) WHERE group_name = %s",
                        (
                            message_con[0],
                            message_con[1],
                        ),
                    )
                    conn.commit()

            elif message_to == "apowrem":
                # part_nam = message_con[0]
                # gp_nam = message_con[1]
                cursor.execute(
                    "SELECT * FROM user_info WHERE username =%s", (message_con[0],)
                )
                res2 = cursor.fetchall()
                conn.commit()
                if len(res2) == 0:
                    print(f"Participant with name {message_con[0]} not exists")
                    ms = "Participant with that name not exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                cursor.execute(
                    "SELECT * FROM groups_info WHERE group_name =%s",
                    (message_con[1],),
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    ms = f"Group with name {message_con[1]} doesnot exists"
                    ms = (ms, "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                for i in res[0][2]:
                    if i == message_con[0]:
                        cursor.execute(
                            "UPDATE groups_info SET group_participants = array_remove(group_participants, %s) WHERE group_name = %s",
                            (
                                message_con[0],
                                message_con[1],
                            ),
                        )
                        conn.commit()

            elif message_to == "GROUP_MESSAGE":
                message_is = message_con[0]
                message_gpn = message_con[1]
                cursor.execute(
                    "SELECT * FROM groups_info WHERE group_name =%s",
                    (message_con[1],),
                )
                res = cursor.fetchall()
                conn.commit()
                if len(res) == 0:
                    ms = f"Group with name {message_con[1]} doesnot exists"
                    ms = (ms , "auth-data")
                    ms = pickle.dumps(ms)
                    serv = "SERVER"
                    serv_he = bytes(f"{len(serv) :<{HEADERLENGTH}}", "utf-8")
                    ms_he = bytes(f"{len(ms) :<{HEADERLENGTH}}", "utf-8")
                    notified_socket.send(
                        serv_he + serv.encode("utf-8") + ms_he + ms
                    )
                group = res[0][2]
                if pickle.loads(user["data"])[1] in group:
                    print(
                        f"Received message from {pickle.loads(user['data'])[1]} to group {message_gpn}"
                    )
                    for i in message_is:
                        bool = 0
                        for client_socket in clients:
                            if pickle.loads(clients[client_socket]["data"])[1] in group:
                                bool = 1
                                if pickle.loads(clients[client_socket]["data"])[1] == i[0]:
                                    print(i[0], pickle.loads(clients[client_socket]["data"])[1]) #pickle.loads(user["data"])[1].encode("utf-8"):
                                    se = bytes(f"{len(pickle.loads(user['data'])[1]) :<{HEADERLENGTH}}","utf-8",)
                                    client_socket.send(
                                        se
                                        + pickle.loads(user["data"])[1].encode("utf-8")
                                        + message["header"]
                                        + pickle.dumps(i[1])
                                    )
                        
                        if (bool == 0):
                            cursor.execute(
                                "INSERT INTO unreadmessages(from_person, to_person, type_of_message, Message) VALUES(%s, %s, %s)",
                                    (
                                        pickle.loads(user["data"])[1],
                                        i[0],
                                        i[1][0],
                                        pickle.dumps(i[1][1]),
                                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                    ),
                            )
                            # print("offline")
                            # i[1][0] image or text
                            # i[1][1] message data




                else:
                    sff = "you are not in this group :)"
                    se = bytes(
                        f"{len(pickle.loads(user['data'])[1]) :<{HEADERLENGTH}}",
                        "utf-8",
                    )
                    client_socket.send(
                        se
                        + pickle.loads(user["data"])[1].encode("utf-8")
                        + message["header"]
                        + sff.encode("utf-8")
                    )

            elif(message_to == "UNREAD-MSSG"):
                user = pickle.loads(user["data"])[1]
                cursor.execute(
                    "SELECT * FROM unreadmessages WHERE to_person =%s", (username,) 
                )
                udat = cursor.fetchall()
                conn.commit()
                for i in udat:
                    sby = i[0]
                    smt = i[2]
                    sme = pickle.loads(i[3])
                    message =(smt, sme)
                    message = pickle.dumps(message)
                    message_he = bytes(f"{len(message)+1 :<{HEADERLENGTH}}", "utf-8")
                    client_socket.send(
                        bytes( f"{len(sby) :<{HEADERLENGTH}}", "utf-8")
                        + sby.encode("utf-8")
                        + message_he
                        + message
                    )   
                cursor.execute(
                    "DELETE FROM unreadmessages WHERE to_person =%s", (username,)
                )
                conn.commit()

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]

cursor.execute("UPDATE user_info SET status=%s", ("offline"))
conn.commit()
conn.close()