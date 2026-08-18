/**
 * stm32f4xx_it.c — interrupt handlers + FreeRTOS exception wiring.
 *
 * The vendored startup file declares SVC_Handler / PendSV_Handler /
 * SysTick_Handler as WEAK infinite loops; the strong definitions here hand
 * them to the FreeRTOS port — without this the scheduler never runs.
 */

#include "stm32f4xx_hal.h"

#include "uart_link.h"

/* FreeRTOS port entry points (port.c) */
extern void xPortSysTickHandler(void);
extern void xPortPendSVHandler(void);
extern void vPortSVCHandler(void);

/* HAL timebase timer (stm32f4xx_hal_timebase_tim.c) */
extern TIM_HandleTypeDef htim6;

void USART6_IRQHandler(void)
{
    HAL_UART_IRQHandler(uart_link_get_handle());
}

void TIM6_DAC_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim6);
}

/* --- FreeRTOS vector bridge --- */

void SVC_Handler(void)
{
    vPortSVCHandler();
}

void PendSV_Handler(void)
{
    xPortPendSVHandler();
}

void SysTick_Handler(void)
{
    xPortSysTickHandler();
}
