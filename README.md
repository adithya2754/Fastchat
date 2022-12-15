# FASTCHAT

### ✨HackStreet Boys✨

## Team members:
- Ravindra Mohith (210050112)
- Adithya Rao (210050060)
- Nithin (210050071)

Our FastChat allow users to send and receive messages and images to other users.

## Working Features

- Creates an account for a client and allows him to login at any time.
- Personal chat between two persons.
- Group creation, Group chat and Admin Powers.
- Image sharing
- End to End Encryption
- Load Balancing of servers

## Tech

- Python
- Postgres
- Socket Library 
- Threading
- Bcrypt Library
- pickle

## Running

- server side:
```sh
python3 load_server.py
python3 master_server.py
python3 server.py $PORT        # Run this as many terminals as you wish with a port number as an argument(Each time you run this a server is created)
```
- client side:
```sh
python3 client.py
```

If there are no servers available, a message "Sorry, No services available" will be printed and the program is terminated else the client is binded to the server which is less busy.

### For Login/Signup..

Program will ask for Login/Signup

- For Login:
      
      Input: LOGIN
      Input: Username
      Input: Password

- For Signup:

      Input: SIGNUP
      Input: Username
      Input: Password

During signup a .pem file is created that stores the private key of the user which is used for decrypting messages. During login we just load this key from that file. This has a demmerit that once a user signup from a device, he has to login from that directory only all the times.

In case of successful login/signup, the program will show the available clients and groups 

### For Personal Chat between two persons...

Our program can send both text messages and images. 

- Login/Signup
- To Enter personal chatroom
   
       Input: 1
       Input: username of person to whom you want to chat with
- For text:

      Input: text 
      Input: message

- For Image:

      Input: image
      Input: path to image

- For leaving chat with that person
    
       Input: 0
       
- To leave this chat room:

       Input: @#@EXIT@#@


If the receiver is offline then the message is stored in the database.

### For Group Creation...

- Login/Signup
- To create a group

      Input: 2
      Input: name of the group you want to create
      Input: names of the participants

- After you entered all the participants name
    
       Input: -1
       
A new group with given name and creator as the admin is created. This data is stored in database

### For Group Chat...

- Login/Signup
- For entering a group chatroom

      Input: 3
      Input: Name of the Group you want to chat with
      
- For Chatting

      Input: 1
      Input: type of image(text or image)
      Input: 0 to stop messaging
      
- For Adding a participant
  
      Input: 2
      Output(if not an admin): Only admin can add/remove partipants
      Input: Participant name
      
- For Removing a participant

      Input: 3
      Output(if not an admin): Only admin can add/remove partipants
      Input: Participant name
      
- For exiting chat with this group

      Input: 0
      
- For leaving this chatroom

      Input: @#@EXIT@#@

## Internal mechanism:

                                               client1 client2 client3  client4
                                                  |      |        |       |
                                                  |      |        |       |
                                                   -----------------------
                                                              |
                                                         load_server
                                                              |
                                                              |
                                                      -----------------
                                                      |       |       |
                                                   server1 server2 server3
                                                      |       |       |
                                                       \      |      /
                                                        \     |     /
                                                        master_server
 
 #### Binding of clients and servers
 - First when we run the load_server.py, it will wait for the connections from clients
 - We also run the master_clients that will wait for servers
 - master_server is connected to all the servers that are currently working
 - Once a client.py is runned, the request is sent to load_server.py, Then it will check for the server which has least no. of clients
 - Then the client binds with that server
 - If a client is connected to a server, we will update this data in the database, From this info we will know how many clients a server is currently handling.
 - We also know which client is connected to which server from this table
  
#### Chatting
- Consider client-A and client-B are connected to server-1. Then if A wants to send message to B the the encrypted message will go to server-1, server-1 sends this message to B, B will decrypt it and read
- If A and B are connected to different servers, let A connected to server-1 and B to server-2. server-1 recieves message from A, since B is not connected to server-1, It will send this message to master_server. The master_server sends the message to server-2 to which B is connected. Then server-2 will send this message to B
- If B is offline then the encrypted message is stored in the database. Once B comes online, he recieves the message through the server he connected from the database

### Encryption
- We used bcrypt for encrypting passwords and stored in database. We took a fixed salt. Since decrypting from encrypted password is not possible, any other person cannot know the password of client even though they have access of database. 
- We used rsa encryption for the messages and send the encrypted message to server. Only the sender and reciever(might be a person(personal message) or a set of people(group message)) will know what the message is.

### Load Balancing
- We distributed the clients among the servers equally using load_server so that the work load is equally balanced. 
- For the intercommunication between the servers we are running the master_server that acts as a intermediate in message transfer from a server to another server 

## Team Members Contribution

Most of the work we have done in team and helped each other

Major contributions:
- Adithya: Personal Chat and Encryption
- Mohith: Group Chat and Load balancing
- Nithin: DataBase and Sphinx
