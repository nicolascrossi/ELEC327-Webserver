#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define IP_HEADER "IP_ADDR"
#define LIGHT_OFF "LIGHT_OFF"
#define LIGHT_ON "LIGHT_ON"

int
main(int argc, char **argv)
{
    char *line = NULL;
    ssize_t line_len = 0;
    int count;

    while (true) {
        printf("Getting line...\n");
        count = getline(&line, &line_len, stdin);
        
        if (count < 0) {
            perror("error reading line");
            free(line);
            line_len = 0;
            // continue;
            break;
        }

        printf("Read line %s", line);

        if (count > sizeof(IP_HEADER) && strncmp(line, IP_HEADER, sizeof(IP_HEADER) - 1) == 0) 
        { // Ensure that there is both IP_HEADER present, some separating character, and at least one character representing the address after
            printf("Received ip: %s", line + sizeof(IP_HEADER));
        } 
        else if (count >= sizeof(LIGHT_OFF) - 1 && strncmp(line, LIGHT_OFF, sizeof(LIGHT_OFF) - 1) == 0)
        { // Just make sure there's enough bytes to compare LIGHT_OFF
            printf("Received light off: %s", line);
        }
        else if (count >= sizeof(LIGHT_ON) - 1 && strncmp(line, LIGHT_ON, sizeof(LIGHT_ON) - 1) == 0)
        { // Just make sure there's enough bytes to compare LIGHT_ON
            printf("Received light on: %s", line);
        }

        free(line);
        line_len = 0;
    }

    printf("Shutting down...\n");

    return 0;
}