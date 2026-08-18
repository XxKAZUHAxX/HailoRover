/**
 * HAL timebase on TIM6 — SysTick is owned by FreeRTOS.
 *
 * The prescaler is derived from the live APB1 timer clock via
 * HAL_RCC_GetPCLK1Freq() (90 MHz post-PLL, ×2 correction applied), so the
 * 1 kHz tick stays correct across the pre-PLL → post-PLL transition in
 * SystemClock_Config(). TIM6 never calls FreeRTOS APIs, so its IRQ can run
 * at priority 5.
 */

#include "stm32f4xx_hal.h"

TIM_HandleTypeDef htim6;

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == TIM6) {
        HAL_IncTick();
    }
}

HAL_StatusTypeDef HAL_InitTick(uint32_t TickPriority)
{
    RCC_ClkInitTypeDef clkconfig;
    uint32_t uwTimclock;
    uint32_t uwAPB1Prescaler;
    uint32_t uwPrescalerValue;
    uint32_t pFLatency;

    HAL_RCC_GetClockConfig(&clkconfig, &pFLatency);

    uwAPB1Prescaler = clkconfig.APB1CLKDivider;
    uwTimclock = HAL_RCC_GetPCLK1Freq();
    if (uwAPB1Prescaler == RCC_HCLK_DIV1) {
        uwTimclock *= 2U;   /* APB1 prescaler 1 → timer clock = PCLK1 (no ×2) */
    }

    uwPrescalerValue = (uint32_t)((uwTimclock / 1000000U) - 1U);

    __HAL_RCC_TIM6_CLK_ENABLE();

    htim6.Instance = TIM6;
    htim6.Init.Period = (1000U / 1U) - 1U;   /* 1 kHz */
    htim6.Init.Prescaler = uwPrescalerValue; /* 1 MHz counter clock */
    htim6.Init.ClockDivision = 0;
    htim6.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim6.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&htim6) != HAL_OK) {
        return HAL_ERROR;
    }

    HAL_NVIC_SetPriority(TIM6_DAC_IRQn, TickPriority, 0U);
    HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);

    return HAL_OK;
}

void HAL_SuspendTick(void)
{
    __HAL_TIM_DISABLE_IT(&htim6, TIM_IT_UPDATE);
}

void HAL_ResumeTick(void)
{
    __HAL_TIM_ENABLE_IT(&htim6, TIM_IT_UPDATE);
}

void HAL_TIM_Base_MspInit(TIM_HandleTypeDef *htim_base)
{
    if (htim_base->Instance == TIM6) {
        __HAL_RCC_TIM6_CLK_ENABLE();
        HAL_NVIC_SetPriority(TIM6_DAC_IRQn, 5U, 0U);
        HAL_NVIC_EnableIRQ(TIM6_DAC_IRQn);
    }
}
