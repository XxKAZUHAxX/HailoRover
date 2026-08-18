/**
 * HAL configuration — only the modules this firmware uses are enabled.
 */

#ifndef STM32F4xx_HAL_CONF_H
#define STM32F4xx_HAL_CONF_H

#ifdef __cplusplus
extern "C" {
#endif

/* Module enables */
#define HAL_MODULE_ENABLED
#define HAL_CORTEX_MODULE_ENABLED
#define HAL_DMA_MODULE_ENABLED
#define HAL_FLASH_MODULE_ENABLED
#define HAL_GPIO_MODULE_ENABLED
#define HAL_PWR_MODULE_ENABLED
#define HAL_RCC_MODULE_ENABLED
#define HAL_TIM_MODULE_ENABLED
#define HAL_UART_MODULE_ENABLED

/* Oscillator values (Hz) — Nucleo-F446RE: 8 MHz HSE crystal */
#define HSE_VALUE         8000000U
#define HSI_VALUE         16000000U
#define LSI_VALUE         32000U
#define LSE_VALUE         32768U
#define EXTERNAL_CLOCK_VALUE 12288000U
#define HSE_STARTUP_TIMEOUT  100U
#define LSE_STARTUP_TIMEOUT  5000U

/* Core / system */
#define VDD_VALUE          3300U
#define TICK_INT_PRIORITY  0x0FU
#define USE_RTOS           0U
#define PREFETCH_ENABLE    1U
#define INSTRUCTION_CACHE_ENABLE 1U
#define DATA_CACHE_ENABLE  1U

#define USE_FULL_ASSERT    0U

/* Full-assert disabled: assert_param compiles away */
#define assert_param(expr) ((void)0U)

/* Includes ------------------------------------------------------------------*/
/* Module headers — mirrors stm32f4xx_hal_conf_template.h. stm32f4xx_hal.h
 * includes ONLY this file, so the module headers (and through them
 * stm32f4xx_hal_def.h → device header → CMSIS types) must be pulled in here. */
#ifdef HAL_RCC_MODULE_ENABLED
  #include "stm32f4xx_hal_rcc.h"
#endif /* HAL_RCC_MODULE_ENABLED */

#ifdef HAL_GPIO_MODULE_ENABLED
  #include "stm32f4xx_hal_gpio.h"
#endif /* HAL_GPIO_MODULE_ENABLED */

#ifdef HAL_DMA_MODULE_ENABLED
  #include "stm32f4xx_hal_dma.h"
#endif /* HAL_DMA_MODULE_ENABLED */

#ifdef HAL_CORTEX_MODULE_ENABLED
  #include "stm32f4xx_hal_cortex.h"
#endif /* HAL_CORTEX_MODULE_ENABLED */

#ifdef HAL_FLASH_MODULE_ENABLED
  #include "stm32f4xx_hal_flash.h"
#endif /* HAL_FLASH_MODULE_ENABLED */

#ifdef HAL_PWR_MODULE_ENABLED
  #include "stm32f4xx_hal_pwr.h"
#endif /* HAL_PWR_MODULE_ENABLED */

#ifdef HAL_TIM_MODULE_ENABLED
  #include "stm32f4xx_hal_tim.h"
#endif /* HAL_TIM_MODULE_ENABLED */

#ifdef HAL_UART_MODULE_ENABLED
  #include "stm32f4xx_hal_uart.h"
#endif /* HAL_UART_MODULE_ENABLED */

#ifdef __cplusplus
}
#endif

#endif /* STM32F4xx_HAL_CONF_H */
