#include <sys/socket.h>
#include <stdio.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdlib.h>

#define NAME "/home/nicorossi/csprojects/ELEC327-Webserver/ipc.sock"
#define BUFSIZE 1024

int
main(int argc, char **argv)
{
    int sock, server_len, msg_sock, bytes_read;
    struct sockaddr_un server;
    char buf[BUFSIZE];

    unlink(NAME);

    sock = socket(AF_LOCAL, SOCK_STREAM, 0);

    if (sock < 0) {
        perror("Error constructing socket");
        exit(1);
    } 
    
    memset(&server, 0, sizeof(struct sockaddr_un));
    server.sun_family = AF_LOCAL;
    memcpy(server.sun_path, NAME, strlen(NAME));

    server_len = sizeof(server.sun_family) + sizeof(server.sun_path);

    if (bind(sock, (struct sockaddr *) &server, server_len) < 0) {
        perror("Error binding socket");
        exit(1);
    }

    if (listen(sock, 5) < 0) {
        perror("Error listening");
        exit(1);
    }

    msg_sock = accept(sock, 0, 0);

    if (msg_sock < 0) {
        perror("Error accepting");
    } else do {
        memset(buf, 0, BUFSIZE);

        bytes_read = read(msg_sock, buf, BUFSIZE);

        if (bytes_read < 0) {
            perror("Error reading message");
        } else if (bytes_read == 0) {
            printf("Closing connection\n");
        } else {
            int i;
            for (i = 0; i < bytes_read; i++) {
                printf("%X\n", buf[i]);
            }
        }
    } while (bytes_read > 0);

    close(msg_sock);
    close(sock);
    unlink(NAME);
}