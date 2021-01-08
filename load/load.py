import socket
import os
import datetime
import signal
import sys
import argparse
import random
import math
from urllib.parse import urlparse

# Define a constant for our buffer size

BUFFER_SIZE = 1024

# A function for creating HTTP GET messages.

def prepare_get_message(host, port, file_name, date=''):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n'
    if date != '':
        request += f'If-modified-since: {date} \r\n'
    request += '\r\n'
    return request


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Read a file from the socket and print it out.  (For errors primarily.)

def print_file_from_socket(sock, bytes_to_read):

    bytes_read = 0
    while (bytes_read < bytes_to_read):
        chunk = sock.recv(BUFFER_SIZE)
        bytes_read += len(chunk)
        print(chunk.decode())

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name, folder, host, port):
    path = os.path.join('C:/Users/nabee/Desktop/assignment2/cache/'+ str(host) + '_' + str(port) + '/' + folder, file_name)

    with open(path, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)


# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '301':
        message = message + value + ' Moved Permanently\r\n' + date_string + '\r\n'
    return message

# Send the given response and file back to the client.

def send_response_to_client(sock, code, file_name, host, port):

    # Determine content type of file

    if ((file_name.endswith('.jpg')) or (file_name.endswith('.jpeg'))):
        type = 'image/jpeg'
    elif (file_name.endswith('.gif')):
        type = 'image/gif'
    elif (file_name.endswith('.png')):
        type = 'image/jpegpng'
    elif ((file_name.endswith('.html')) or (file_name.endswith('.htm'))):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    # Construct header and send it

    header = prepare_response_message(code) + 'Location: http://' + str(host) + ':' + str(port) + '/' + file_name + '\r\n\r\n'
    print(header)
    sock.send(header.encode())

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# //////////////////////////////MAIN//////////////////////////////////////////////////////////

# Our main function.


def main():
    # the test file
    file_name = "map.jpg"

    # make sure it runs forever
    while(1):
        # create a list of the servers from the command line
        servers = []
        for i, arg in enumerate(sys.argv):
            if i > 0:
                servers.append(arg)
        client_sockets = []
        transfer_times = []

        # perform the test for each server
        for i in range(len(servers)):
            try:
                # start timing file transfer
                start = datetime.datetime.now()
                client_sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                client_sockets[i].connect((servers[i].split(":")[0], int(servers[i].split(":")[1])))
            except ConnectionRefusedError:
                print('Error:  That host or port is not accepting connections.')
                sys.exit(1)


            # The connection was successful, so we can prep and send our message.

            print('Connection to server established. Sending message...\n')
            message = prepare_get_message(servers[i].split(":")[0], int(servers[i].split(":")[1]), file_name, 'Sun, 06 Nov 1994 08:49:37 GMT')
            client_sockets[i].send(message.encode())

            # Receive the response from the server and start taking a look at it

            response_line = get_line_from_socket(client_sockets[i])
            response_list = response_line.split(' ')
            headers_done = False

            # If an error is returned from the server, we dump everything sent and
            # exit right away.

            if response_list[1] != '200':
                print('Error:  An error response was received from the server.  Details:\n')
                print(response_line);
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(client_sockets[i])
                    print(header_line)
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                print_file_from_socket(client_sockets[i], bytes_to_read)
                sys.exit(1)


            # If it's OK, we retrieve and write the file out.

            else:


                # If requested file begins with a / we strip it off.
                while (file_name[0] == '/'):
                    file_name = file_name[1:]

                # get the actual file
                file = (file_name.split('/')[len(file_name.split('/'))-1])

                # Go through headers and find the size of the file, then save it.
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(client_sockets[i])
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
            end = datetime.datetime.now()
            # add transfer time to an array of tuples with the server and its transfer time
            transfer_times.append((servers[i], (start-end).seconds/60))

        # sort the array by transfer times
        sorted(transfer_times, key=lambda k: k[1])

        # give the servers priority based on speed
        distribution_number = 0
        for i in range(len(servers)):
            distribution_number += i +1
        value = random.randint(1, distribution_number)

        x = 0
        for i in range(len(servers)):
            x += i + 1
            if value <= x:
                chosen_server_host = servers[i].split(":")[0]
                chosen_server_port = int(servers[i].split(":")[1])
                break

        # send the respone to the client
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(30)
        try:
            server_socket.bind(('', 0))
            print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
            server_socket.listen(1)
            print('Waiting for incoming client connection ...')
            conn, addr = server_socket.accept()
            print('Accepted connection from client address:', addr)
            print('Connection to client established, waiting to receive message...')

            # We obtain our request from the socket.  We look at the request and
            # figure out what to do based on the contents of things.

            request = get_line_from_socket(conn)
            print('Received request:  ' + request)
            request_list = request.split()

            # This server doesn't care about headers, so we just clean them up.

            while (get_line_from_socket(conn) != ''):
                pass

            # If we did not get a GET command respond with a 501.

            if request_list[0] != 'GET':
                print('Invalid type of request received ... responding with error!')
                send_response_to_client(conn, '501', '501.html', chosen_server_host, chosen_server_port)

            # If we did not get the proper HTTP version respond with a 505.

            elif request_list[2] != 'HTTP/1.1':
                print('Invalid HTTP version received ... responding with error!')
                send_response_to_client(conn, '505', '505.html', chosen_server_host, chosen_server_port)

            # We have the right request and version, so check if file exists.

            else:

                # If requested file begins with a / we strip it off.

                req_file = request_list[1]
                while (req_file[0] == '/'):
                    req_file = req_file[1:]

                # send the 301 response
                print('Sending response to client')
                send_response_to_client(conn, '301', req_file, chosen_server_host, chosen_server_port)
        except socket.timeout:
            print("Timeout Error\n\n\n")






if __name__ == '__main__':
    main()

