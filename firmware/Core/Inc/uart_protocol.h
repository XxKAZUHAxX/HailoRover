/**
 * UART Binary Protocol — RPi ↔ STM32 Motor Controller
 *
 * Packet format:
 *   [START 0xAA] [CMD 1B] [LEN 1B] [PAYLOAD N bytes] [CRC8 1B]
 *
 * Commands:
 *   0x01 DRIVE  — payload: left_speed (int8), right_speed (int8)
 *   0x02 STOP   — no payload
 *   0x03 PING   — no payload, respond with status byte
 *   0x04 BRAKE  — no payload
 */

#ifndef UART_PROTOCOL_H
#define UART_PROTOCOL_H

#include <stdint.h>

#define PROTOCOL_START_BYTE  0xAA
#define PROTOCOL_CMD_DRIVE   0x01
#define PROTOCOL_CMD_STOP    0x02
#define PROTOCOL_CMD_PING    0x03
#define PROTOCOL_CMD_BRAKE   0x04

#define PROTOCOL_MAX_PAYLOAD 16

typedef struct {
    uint8_t command;
    uint8_t length;
    uint8_t payload[PROTOCOL_MAX_PAYLOAD];
} protocol_packet_t;

#endif /* UART_PROTOCOL_H */
