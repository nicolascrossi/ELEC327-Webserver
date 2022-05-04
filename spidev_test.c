/*
 * SPI testing utility (using spidev driver)
 *
 * Copyright (c) 2007  MontaVista Software, Inc.
 * Copyright (c) 2007  Anton Vorontsov <avorontsov@ru.mvista.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 *
 * Cross-compile with cross-gcc -I/path/to/cross-kernel/include
 */

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>
#include <stdbool.h>
#include <string.h>

// These are the headers for the messages coming from the server
#define IP_ADDR "IP_ADDR"
#define LIGHT_ON "LIGHT_ON"
#define LIGHT_OFF "LIGHT_OFF"
#define PRANK_ON "PRANK_ON"

// The values used for SPI
#define END 1 				// Signifies the end of the message
#define LIGHT_OFF_CODE 2
#define LIGHT_ON_CODE 3
#define IP_ADDR_CODE 4
#define PRANK_ON_CODE 5
#define MSG_LEN 2			// Length of the messages without data

// Functiont to handle potential errors
static void pabort(const char *s)
{
	perror(s);
	abort();
}

// Various variables to store relevant settings
static const char *device = "/dev/spidev0.0";
static uint8_t mode;
static uint8_t bits = 8;
static uint32_t speed = 500000;
static uint16_t delay;

// Predefined SPI messages when possible
static uint8_t msg_off[MSG_LEN] = {LIGHT_OFF_CODE, END};
static uint8_t msg_on[MSG_LEN] = {LIGHT_ON_CODE, END};
static uint8_t msg_prank_on[MSG_LEN] = {PRANK_ON_CODE, END};

// Transfers the message tx of length len to the file descriptor fd using SPI and the saved settings
static void transfer(int fd, uint8_t *tx, uint8_t len)
{
	// For monitoring. Displays the contents of the message about to be sent
	uint8_t i;
	for (i = 0; i < len; i++) {
		printf("%X ", tx[i]);
	}
	printf("\n");
	
	int ret; // The return value of the attempted SPI transfer
	// uint8_t tx[] = {
    //     0x48, 0x45, 0x4C, 0x4C, 0x4F,
    //     0x20, 
    //     0x57, 0x4F, 0x52, 0x4C, 0x44,
    //     0x0A 
	// };
	// uint8_t rx[len] = {0, };
	uint8_t *rx = malloc(len); // Buffer for the response (essentially unused)
	memset(rx, 0, len);
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = len,
		.delay_usecs = delay,
		.speed_hz = speed,
		.bits_per_word = bits,
	};

	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr); // Actually send message
	if (ret < 1)
		pabort("can't send spi message");

	free(rx);
    /*
	for (ret = 0; ret < ARRAY_SIZE(tx); ret++) {
		if (!(ret % 6))
			puts("");
		printf("%.2X ", rx[ret]);
	}
	puts("");
    */
}

// Help function to indicate how to call the program
static void print_usage(const char *prog)
{
	printf("Usage: %s [-DsbdlHOLC3]\n", prog);
	puts("  -D --device   device to use (default /dev/spidev1.1)\n"
	     "  -s --speed    max speed (Hz)\n"
	     "  -d --delay    delay (usec)\n"
	     "  -b --bpw      bits per word \n"
	     "  -l --loop     loopback\n"
	     "  -H --cpha     clock phase\n"
	     "  -O --cpol     clock polarity\n"
	     "  -L --lsb      least significant bit first\n"
	     "  -C --cs-high  chip select active high\n"
	     "  -3 --3wire    SI/SO signals shared\n");
	exit(1);
}

// Parses the options given to the program
static void parse_opts(int argc, char *argv[])
{
	while (1) {
		static const struct option lopts[] = {
			{ "device",  1, 0, 'D' },
			{ "speed",   1, 0, 's' },
			{ "delay",   1, 0, 'd' },
			{ "bpw",     1, 0, 'b' },
			{ "loop",    0, 0, 'l' },
			{ "cpha",    0, 0, 'H' },
			{ "cpol",    0, 0, 'O' },
			{ "lsb",     0, 0, 'L' },
			{ "cs-high", 0, 0, 'C' },
			{ "3wire",   0, 0, '3' },
			{ "no-cs",   0, 0, 'N' },
			{ "ready",   0, 0, 'R' },
			{ NULL, 0, 0, 0 },
		};
		int c;

		c = getopt_long(argc, argv, "D:s:d:b:lHOLC3NR", lopts, NULL);

		if (c == -1)
			break;

		switch (c) {
		case 'D':
			device = optarg;
			break;
		case 's':
			speed = atoi(optarg);
			break;
		case 'd':
			delay = atoi(optarg);
			break;
		case 'b':
			bits = atoi(optarg);
			break;
		case 'l':
			mode |= SPI_LOOP;
			break;
		case 'H':
			mode |= SPI_CPHA;
			break;
		case 'O':
			mode |= SPI_CPOL;
			break;
		case 'L':
			mode |= SPI_LSB_FIRST;
			break;
		case 'C':
			mode |= SPI_CS_HIGH;
			break;
		case '3':
			mode |= SPI_3WIRE;
			break;
		case 'N':
			mode |= SPI_NO_CS;
			break;
		case 'R':
			mode |= SPI_READY;
			break;
		default:
			print_usage(argv[0]);
			break;
		}
	}
}

int main(int argc, char *argv[])
{
	int ret = 0;
	int fd;

	parse_opts(argc, argv);

	fd = open(device, O_RDWR);
	if (fd < 0)
		pabort("can't open device");

	/*
	 * spi mode
	 */
	ret = ioctl(fd, SPI_IOC_WR_MODE, &mode);
	if (ret == -1)
		pabort("can't set spi mode");

	ret = ioctl(fd, SPI_IOC_RD_MODE, &mode);
	if (ret == -1)
		pabort("can't get spi mode");

	/*
	 * bits per word
	 */
	ret = ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't set bits per word");

	ret = ioctl(fd, SPI_IOC_RD_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't get bits per word");

	/*
	 * max speed hz
	 */
	ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't set max speed hz");

	ret = ioctl(fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't get max speed hz");

	printf("spi mode: %d\n", mode);
	printf("bits per word: %d\n", bits);
	printf("max speed: %d Hz (%d KHz)\n", speed, speed/1000);

	// transfer(fd);

	// Enter the loop for parsing the output from the server
	char *line = NULL; // Line read from stdin
	ssize_t line_len = 0; // Length of line
	int count; // Number of characters read

	while (true) {
		printf("Getting line...\n");
		// getline will allocate memory as needed if line is NULL and line_len 0
		count = getline(&line, &line_len, stdin); // Blocks until a line is available

		if (count < 0) { // Most likely the server was shutdown
			perror("Error reading line");
			free(line);
			break;
		}

		printf("Read line \"%s\"", line);

		// Chech if we've received an IP
		if (count > sizeof(IP_ADDR) && strncmp(line, IP_ADDR, sizeof(IP_ADDR) - 1) == 0)
		{
			printf("Received IP: %s", line + sizeof(IP_ADDR));

			// [IP_ADDR_CODE, length of IP, ip bytes start, ..., ip bytes end, END]
			line[sizeof(IP_ADDR) - 1] =  count - sizeof(IP_ADDR) - 1 + 1; // Set the length of the IP string
			line[sizeof(IP_ADDR) - 2] = IP_ADDR_CODE; // Indicate this is an IP message
			line[count - 1] = END; // Add the message end indicator
			transfer(fd, (uint8_t *) line + sizeof(IP_ADDR) - 2, count - sizeof(IP_ADDR) - 1 + 2 + 1);
		}
		// Check if we've received light off
		else if (count >= sizeof(LIGHT_OFF) - 1 && strncmp(line, LIGHT_OFF, sizeof(LIGHT_OFF) - 1) == 0)
		{
			printf("Received LIGHT_OFF: %s", line);
			transfer(fd, msg_off, MSG_LEN);
		}
		// Check if we've receieved light on
		else if (count >= sizeof(LIGHT_ON) - 1 && strncmp(line, LIGHT_ON, sizeof(LIGHT_ON) - 1) == 0)
		{
			printf("Received LIGHT_ON: %s", line);
			transfer(fd, msg_on, MSG_LEN);
		}
		// Check if we've received prank mode on
		else if (count >= sizeof(PRANK_ON) - 1 && strncmp(line, PRANK_ON, sizeof(PRANK_ON) - 1) == 0)
		{
			printf("Received PRANK_ON: %s", line);
			transfer(fd, msg_prank_on, MSG_LEN);
		}

		// Reset variables to get the next line
		free(line);
		line_len = 0;
	}

	printf("Shutting down...\n");

	close(fd);

	return ret;
}