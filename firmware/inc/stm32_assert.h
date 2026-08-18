/**
 * Assert stub — USE_FULL_ASSERT is disabled (see stm32f4xx_hal_conf.h).
 */

#ifndef STM32_ASSERT_H
#define STM32_ASSERT_H

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line);
#endif

#endif /* STM32_ASSERT_H */
