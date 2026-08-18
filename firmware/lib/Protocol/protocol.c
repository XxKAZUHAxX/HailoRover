/**
 * protocol.c — pure UART frame parser + CRC-8 (hardware-independent).
 *
 * CRC-8-ATM: poly 0x07, init 0x00, MSB-first, no reflection, no final XOR.
 * Byte-for-byte equivalent of raspi/server/app/hal/uart_hal.py:_crc8().
 * Verified by firmware/tools/crc_parity_check.py.
 */

#include <stddef.h>

#include "uart_protocol.h"

/* --------------------------------------------------------------------------
 * CRC-8-ATM
 * ------------------------------------------------------------------------*/

static uint8_t crc8_update(uint8_t crc, uint8_t byte)
{
    uint8_t i;

    crc ^= byte;
    for (i = 0U; i < 8U; i++) {
        if ((crc & 0x80U) != 0U) {
            crc = (uint8_t)((crc << 1U) ^ 0x07U);
        } else {
            crc = (uint8_t)(crc << 1U);
        }
    }
    return crc;
}

uint8_t protocol_crc8(const uint8_t *data, uint32_t len)
{
    uint8_t crc = 0x00U;
    uint32_t i;

    for (i = 0U; i < len; i++) {
        crc = crc8_update(crc, data[i]);
    }
    return crc;
}

/* --------------------------------------------------------------------------
 * RX state machine (byte-wise)
 *
 * Resync behavior: stray bytes are ignored until a 0xAA arrives in the IDLE
 * state; a 0xAA inside the payload is harmless (only treated as START when
 * idle); a bad LEN or CRC drops the frame and resyncs on the next 0xAA.
 * ------------------------------------------------------------------------*/

typedef enum {
    RX_WAIT_START,
    RX_WAIT_CMD,
    RX_WAIT_LEN,
    RX_WAIT_PAYLOAD,
    RX_WAIT_CRC
} rx_state_t;

static rx_state_t          rx_state = RX_WAIT_START;
static uint8_t             rx_buf[PROTOCOL_FRAME_MAX_SIZE];
static uint8_t             rx_idx;
static uint8_t             rx_payload_len;
static uint8_t             rx_crc;
static protocol_packet_t   rx_packet;

void protocol_reset(void)
{
    rx_state = RX_WAIT_START;
    rx_idx = 0U;
    rx_payload_len = 0U;
    rx_crc = 0x00U;
}

const protocol_packet_t *protocol_rx_byte(uint8_t byte)
{
    const protocol_packet_t *result = NULL;

    switch (rx_state) {
    case RX_WAIT_START:
        if (byte == PROTOCOL_START_BYTE) {
            rx_buf[0] = byte;
            rx_idx = 1U;
            rx_crc = 0x00U;
            rx_crc = crc8_update(rx_crc, byte);
            rx_state = RX_WAIT_CMD;
        }
        break;

    case RX_WAIT_CMD:
        rx_buf[rx_idx] = byte;
        rx_idx++;
        rx_crc = crc8_update(rx_crc, byte);
        rx_state = RX_WAIT_LEN;
        break;

    case RX_WAIT_LEN:
        rx_buf[rx_idx] = byte;
        rx_idx++;
        rx_crc = crc8_update(rx_crc, byte);
        if (byte > PROTOCOL_MAX_PAYLOAD) {
            /* Corrupt length — resync on the next 0xAA */
            rx_state = RX_WAIT_START;
            break;
        }
        rx_payload_len = byte;
        rx_state = (byte == 0U) ? RX_WAIT_CRC : RX_WAIT_PAYLOAD;
        break;

    case RX_WAIT_PAYLOAD:
        rx_buf[rx_idx] = byte;
        rx_idx++;
        rx_crc = crc8_update(rx_crc, byte);
        if (rx_idx >= (PROTOCOL_HEADER_SIZE + rx_payload_len)) {
            rx_state = RX_WAIT_CRC;
        }
        break;

    case RX_WAIT_CRC:
        if (byte == rx_crc) {
            rx_packet.command = rx_buf[1];
            rx_packet.length = rx_payload_len;
            for (uint8_t i = 0U; i < rx_payload_len; i++) {
                rx_packet.payload[i] = rx_buf[PROTOCOL_HEADER_SIZE + i];
            }
            result = &rx_packet;
        }
        /* CRC failure: drop frame, resync on the next 0xAA */
        rx_state = RX_WAIT_START;
        break;

    default:
        rx_state = RX_WAIT_START;
        break;
    }

    return result;
}
