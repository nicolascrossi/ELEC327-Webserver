LANG = gcc

CFLAGS = -g -Wall -Wextra -Werror

ipc: ipc.o
	gcc ipc.o -o ipc_server

ipc.o: ipc.c
	gcc -c ipc.c -o ipc.o