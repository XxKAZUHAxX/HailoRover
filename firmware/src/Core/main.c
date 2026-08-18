/**
 * main.c — HailoRover motor-controller firmware entry (STM32F446RE).
 *
 * Boot order:
 *   1. HAL_Init (TIM6 timebase — SysTick belongs to FreeRTOS)
 *   2. SystemClock_Config (HSE 8 MHz → PLL → 180 MHz)
 *   3. uart_link_init (USART6, first per-byte RX armed)
 *   4. motor_init (coast + STBY high + 20 kHz PWM)
 *   5. app_freertos_init (static tasks/queues) → scheduler start
 *
 * Safe idle: with the Pi's motor_enabled=false the link is silent and the
 * motors remain coasted — the watchdog never even triggers.
 */

#include "FreeRTOS.h"
#include "task.h"

#include "main.h"
#include "motor_control.h"
#include "pin_config.h"
#include "stm32f4xx_hal.h"
#include "uart_link.h"

static void MX_GPIO_Init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();

    gpio.Pin = LED_GPIO_PIN;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_GPIO_PORT, &gpio);
}

void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    /* 180 MHz SYSCLK: HSE 8 MHz → PLLM4 / PLLN180 / PLLP2 (HCLK 180) */
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLM = 4;
    osc.PLL.PLLN = 180;
    osc.PLL.PLLP = RCC_PLLP_DIV2;
    osc.PLL.PLLQ = 8;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        Error_Handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV4;   /* APB1 = 45 MHz (TIM 90 MHz) */
    clk.APB2CLKDivider = RCC_HCLK_DIV2;   /* APB2 = 90 MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_5) != HAL_OK) {
        Error_Handler();
    }
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();

    uart_link_init();
    motor_init();
    app_freertos_init();

    vTaskStartScheduler();

    /* Never reached — scheduler failure */
    Error_Handler();
}

void Error_Handler(void)
{
    __disable_irq();
    for (;;) {
    }
}
