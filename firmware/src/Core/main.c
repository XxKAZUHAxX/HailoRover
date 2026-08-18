/**
 * HailoRover motor-controller firmware — STM32F446RE.
 *
 * M1 milestone: 180 MHz clock + LED heartbeat.
 * M2 adds: USART6 protocol link, TIM2 PWM motor control, FreeRTOS tasks.
 */

#include "main.h"
#include "pin_config.h"
#include "stm32f4xx_hal.h"

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

    for (;;) {
        HAL_GPIO_TogglePin(LED_GPIO_PORT, LED_GPIO_PIN);
        HAL_Delay(500);
    }
}

void Error_Handler(void)
{
    __disable_irq();
    for (;;) {
    }
}
