LANG = gcc

CFLAGS = -g -Wall -Wextra -Werror

stdin_recv: stdin_recv.c
	gcc -o stdin_recv stdin_recv.c

spidev_test: spidev_test.c
	gcc -o spidev_test spidev_test.c