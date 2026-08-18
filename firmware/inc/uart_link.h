/**
 * UART link layer — USART6 HAL glue for the RPi protocol.
 *
 * Owns the UART handle, arms the per-byte receive interrupt, feeds the pure
 * parser (lib/Protocol), forwards complete packets to the FreeRTOS queue,
 * and transmits the single-byte PING response. Nothing else ever transmits.
 */

#ifndef UART_LINK_H
#define UART_LINK_H

#include "stm32f4xx_hal.h"

void uart_link_init(void);
void uart_link_send_ping_response(void);
UART_HandleTypeDef *uart_link_get_handle(void);

#endif /* UART_LINK_H */
