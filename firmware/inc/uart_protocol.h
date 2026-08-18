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
 *
 * CRC-8-ATM (poly 0x07, init 0x00, MSB-first, no reflection, no final XOR)
 * covers every byte of the frame INCLUDING the start byte — byte-for-byte
 * equivalent of raspi/server/app/hal/uart_hal.py:_crc8().
 *
 * Wire contract: the STM32 replies ONLY to PING, with exactly one byte 0x00.
 * Nothing else is ever transmitted (the Pi's ping reads 1 byte with a 50 ms
 * timeout; stray bytes corrupt its status check). PLAN.md's older ACK/NACK
 * idea is superseded by this rule.
 *
 * This header is HAL-free — the parser lives in lib/Protocol/, the UART
 * link layer in src/Core/uart_link.c (see inc/uart_link.h).
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

/* Frame layout constants */
#define PROTOCOL_HEADER_SIZE      3U   /* 0xAA + CMD + LEN */
#define PROTOCOL_FRAME_MAX_SIZE   (PROTOCOL_HEADER_SIZE + PROTOCOL_MAX_PAYLOAD + 1U)

typedef struct {
    uint8_t command;
    uint8_t length;
    uint8_t payload[PROTOCOL_MAX_PAYLOAD];
} protocol_packet_t;

/* Pure parser (lib/Protocol/protocol.c) — hardware-independent */
uint8_t protocol_crc8(const uint8_t *data, uint32_t len);
const protocol_packet_t *protocol_rx_byte(uint8_t byte);
void protocol_reset(void);

#endif /* UART_PROTOCOL_H */
