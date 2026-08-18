/**
 * uart_link.c — USART6 HAL glue for the RPi protocol link (115200 8N1).
 *
 * Owns the UART handle, arms the per-byte receive interrupt, feeds the pure
 * parser (lib/Protocol), forwards complete packets to the rx queue from the
 * ISR (USART6 IRQ priority = configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY),
 * and transmits the single-byte PING response.
 *
 * Wire contract: ONLY the 0x00 PING reply is ever transmitted on this UART.
 */

#include "FreeRTOS.h"
#include "queue.h"
#include "stm32f4xx_hal.h"

#include "pin_config.h"
#include "uart_link.h"
#include "uart_protocol.h"

/* Externals from app_tasks.c */
extern QueueHandle_t g_uart_rx_queue;
extern volatile uint8_t g_uart_rx_byte;

static UART_HandleTypeDef huart6;

UART_HandleTypeDef *uart_link_get_handle(void)
{
    return &huart6;
}

void uart_link_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART6_CLK_ENABLE();

    /* USART6: TX = PC6, RX = PC7 (AF8) */
    gpio.Pin = UART_TX_GPIO_PIN | UART_RX_GPIO_PIN;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    gpio.Alternate = UART_GPIO_AF;
    HAL_GPIO_Init(UART_TX_GPIO_PORT, &gpio);

    huart6.Instance = UART_PERIPH;
    huart6.Init.BaudRate = UART_BAUDRATE;
    huart6.Init.WordLength = UART_WORDLENGTH_8B;
    huart6.Init.StopBits = UART_STOPBITS_1;
    huart6.Init.Parity = UART_PARITY_NONE;
    huart6.Init.Mode = UART_MODE_TX_RX;
    huart6.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart6.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart6);

    HAL_NVIC_SetPriority(USART6_IRQn, 5U, 0U);   /* = configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY */
    HAL_NVIC_EnableIRQ(USART6_IRQn);

    /* Arm the first per-byte receive */
    HAL_UART_Receive_IT(&huart6, (uint8_t *)&g_uart_rx_byte, 1U);
}

static void uart_link_rearm(void)
{
    HAL_UART_Receive_IT(&huart6, (uint8_t *)&g_uart_rx_byte, 1U);
}

void uart_link_send_ping_response(void)
{
    static const uint8_t ping_ok = 0x00U;   /* must stay alive until TX complete */
    (void)HAL_UART_Transmit_IT(&huart6, (uint8_t *)&ping_ok, 1U);
}

/* --------------------------------------------------------------------------
 * HAL callbacks (USART6 IRQ context — FreeRTOS-ISR-safe at priority 5)
 * ------------------------------------------------------------------------*/

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    BaseType_t higher_priority_woken = pdFALSE;

    if (huart->Instance != UART_PERIPH) {
        return;
    }

    const protocol_packet_t *pkt = protocol_rx_byte(g_uart_rx_byte);
    if (pkt != NULL) {
        (void)xQueueSendFromISR(g_uart_rx_queue, pkt, &higher_priority_woken);
        portYIELD_FROM_ISR(higher_priority_woken);
    }
    uart_link_rearm();
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance != UART_PERIPH) {
        return;
    }
    /* Overrun / framing error: drop the partial frame and re-arm so RX can
     * never silently die. */
    protocol_reset();
    uart_link_rearm();
}
