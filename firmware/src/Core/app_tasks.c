/**
 * app_tasks.c — FreeRTOS tasks, queues (all static allocation), and hooks.
 *
 * Task model (priorities 4..0):
 *   uart_rx_task (2): rx_q → PING reply | motor_q forwarding
 *   motor_task   (1): motor_q → drive/stop/brake + coast watchdog
 *
 * Watchdog: the motor task is the SINGLE writer of motor state. Its 100 ms
 * queue-timeout branch checks the DRIVE deadline (wrap-safe tick math) and
 * coasts when exceeded — no separate timer/task can race an in-flight DRIVE.
 */

#include "FreeRTOS.h"
#include "queue.h"
#include "task.h"

#include "motor_control.h"
#include "pin_config.h"
#include "stm32f4xx_hal.h"
#include "uart_link.h"
#include "uart_protocol.h"

/* --------------------------------------------------------------------------
 * Static task/queue storage (configSUPPORT_DYNAMIC_ALLOCATION = 0)
 * ------------------------------------------------------------------------*/

#define QUEUE_SLOTS 4U

static StackType_t     uart_task_stack[256];
static StaticTask_t    uart_task_tcb;
static StackType_t     motor_task_stack[256];
static StaticTask_t    motor_task_tcb;
static StackType_t     idle_task_stack[configMINIMAL_STACK_SIZE];
static StaticTask_t    idle_task_tcb;

static uint8_t         rx_q_storage[QUEUE_SLOTS * sizeof(protocol_packet_t)];
static StaticQueue_t   rx_q_ctrl;
static uint8_t         motor_q_storage[QUEUE_SLOTS * sizeof(protocol_packet_t)];
static StaticQueue_t   motor_q_ctrl;

QueueHandle_t          g_uart_rx_queue = NULL;
static QueueHandle_t   motor_q = NULL;

/* ISR-owned byte buffer for the per-byte UART receive */
volatile uint8_t       g_uart_rx_byte = 0U;

/* --------------------------------------------------------------------------
 * Task bodies
 * ------------------------------------------------------------------------*/

static void uart_rx_task(void *arg)
{
    protocol_packet_t pkt;

    (void)arg;
    for (;;) {
        if (xQueueReceive(g_uart_rx_queue, &pkt, portMAX_DELAY) == pdTRUE) {
            if (pkt.command == PROTOCOL_CMD_PING) {
                /* The ONLY thing ever transmitted on the link */
                uart_link_send_ping_response();
            } else {
                (void)xQueueSend(motor_q, &pkt, 0U);
            }
        }
    }
}

static void motor_task(void *arg)
{
    protocol_packet_t pkt;
    TickType_t last_cmd;

    (void)arg;
    last_cmd = xTaskGetTickCount();

    for (;;) {
        if (xQueueReceive(motor_q, &pkt, pdMS_TO_TICKS(100U)) == pdTRUE) {
            switch (pkt.command) {
            case PROTOCOL_CMD_DRIVE:
                if (pkt.length == 2U) {
                    motor_set_left((int8_t)pkt.payload[0]);
                    motor_set_right((int8_t)pkt.payload[1]);
                    /* Only DRIVE arms the watchdog */
                    last_cmd = xTaskGetTickCount();
                }
                break;

            case PROTOCOL_CMD_STOP:
                motor_stop();
                break;

            case PROTOCOL_CMD_BRAKE:
                motor_brake();
                break;

            default:
                break;
            }
        } else {
            /* Queue idle — watchdog check (wrap-safe unsigned math) */
            if ((xTaskGetTickCount() - last_cmd) >= pdMS_TO_TICKS(WATCHDOG_COAST_TIMEOUT_MS)) {
                motor_stop();   /* coast */
                last_cmd = xTaskGetTickCount();
            }
        }
    }
}

/* --------------------------------------------------------------------------
 * FreeRTOS static-allocation hooks
 * ------------------------------------------------------------------------*/

void vApplicationGetIdleTaskMemory(StaticTask_t **ppxIdleTaskTCBBuffer,
                                   StackType_t **ppxIdleTaskStackBuffer,
                                   uint32_t *pulIdleTaskStackSize)
{
    *ppxIdleTaskTCBBuffer = &idle_task_tcb;
    *ppxIdleTaskStackBuffer = idle_task_stack;
    *pulIdleTaskStackSize = configMINIMAL_STACK_SIZE;
}

void vApplicationGetTimerTaskMemory(StaticTask_t **ppxTimerTaskTCBBuffer,
                                    StackType_t **ppxTimerTaskStackBuffer,
                                    uint32_t *pulTimerTaskStackSize)
{
    /* configUSE_TIMERS = 0 — the timer task never runs; these buffers are
     * never used but the hooks must exist when static allocation is on. */
    static StaticTask_t timer_task_tcb;
    static StackType_t  timer_task_stack[configMINIMAL_STACK_SIZE];

    *ppxTimerTaskTCBBuffer = &timer_task_tcb;
    *ppxTimerTaskStackBuffer = timer_task_stack;
    *pulTimerTaskStackSize = configMINIMAL_STACK_SIZE;
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;
    /* Fault pattern on LD2: rapid blink, then halt */
    for (;;) {
        HAL_GPIO_TogglePin(LED_GPIO_PORT, LED_GPIO_PIN);
        for (volatile uint32_t i = 0U; i < 1000000U; i++) {
        }
    }
}

/* --------------------------------------------------------------------------
 * Init
 * ------------------------------------------------------------------------*/

void app_freertos_init(void)
{
    g_uart_rx_queue = xQueueCreateStatic(QUEUE_SLOTS, sizeof(protocol_packet_t),
                                         rx_q_storage, &rx_q_ctrl);
    motor_q = xQueueCreateStatic(QUEUE_SLOTS, sizeof(protocol_packet_t),
                                 motor_q_storage, &motor_q_ctrl);

    (void)xTaskCreateStatic(uart_rx_task, "uart_rx", 256U, NULL, 2U,
                            uart_task_stack, &uart_task_tcb);
    (void)xTaskCreateStatic(motor_task, "motor", 256U, NULL, 1U,
                            motor_task_stack, &motor_task_tcb);
}
