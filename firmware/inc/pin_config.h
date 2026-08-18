/**
 * Pin map — Nucleo-F446RE defaults (adjust to actual wiring).
 * Board refs: UM1724 Table 19 (Arduino connector), DS10693 AF table.
 */

#ifndef PIN_CONFIG_H
#define PIN_CONFIG_H

/* ---------------- UART link to Pi (USART6) ----------------
 * NOT USART2: PA2/PA3 is the ST-Link VCP on this board (solder bridges
 * SB13/SB14). USART6 on PC6/PC7 is free and direct-wired to the Pi. */
#define UART_PERIPH           USART6
#define UART_TX_GPIO_PORT     GPIOC
#define UART_TX_GPIO_PIN      GPIO_PIN_6   /* USART6_TX, AF8 */
#define UART_RX_GPIO_PORT     GPIOC
#define UART_RX_GPIO_PIN      GPIO_PIN_7   /* USART6_RX, AF8 */
#define UART_GPIO_AF          GPIO_AF8_USART6
#define UART_BAUDRATE         115200U

/* ---------------- Motor PWM — TIM2 CH1/CH2 on PA0/PA1 (AF1) ----------------
 * TIM2 is on APB1: timer clock = 90 MHz at 180 MHz SYSCLK. */
#define MOTOR_TIM                      TIM2
#define MOTOR_PWM_TIMER_CLOCK_HZ       90000000UL
#define MOTOR_PWM_HZ                   20000UL
#define MOTOR_PWM_PERIOD               ((MOTOR_PWM_TIMER_CLOCK_HZ / MOTOR_PWM_HZ) - 1UL)  /* 4499 */
#define MOTOR_PWM_LEFT_CHANNEL         TIM_CHANNEL_1
#define MOTOR_PWM_RIGHT_CHANNEL        TIM_CHANNEL_2
#define MOTOR_PWM_GPIO_PORT            GPIOA
#define MOTOR_PWM_LEFT_PIN             GPIO_PIN_0   /* A0 */
#define MOTOR_PWM_RIGHT_PIN            GPIO_PIN_1   /* A1 */
#define MOTOR_PWM_GPIO_AF              GPIO_AF1_TIM2

/* Alternative for 180 MHz timer clock (ARR 8999): TIM1 CH1/CH2 on PA8/PA9 (AF1),
 * needs MOE enable (HAL_TIM_PWM_Start handles it). */

/* ---------------- Direction + standby (TB6612FNG) ----------------
 * AIN1/AIN2 = left, BIN1/BIN2 = right, STBY must stay HIGH. */
#define MOTOR_L_IN1_PORT  GPIOC
#define MOTOR_L_IN1_PIN   GPIO_PIN_0   /* A5 */
#define MOTOR_L_IN2_PORT  GPIOC
#define MOTOR_L_IN2_PIN   GPIO_PIN_1   /* A4 */
#define MOTOR_R_IN1_PORT  GPIOC
#define MOTOR_R_IN1_PIN   GPIO_PIN_2
#define MOTOR_R_IN2_PORT  GPIOC
#define MOTOR_R_IN2_PIN   GPIO_PIN_3
#define MOTOR_STBY_PORT   GPIOC
#define MOTOR_STBY_PIN    GPIO_PIN_4

/* DRV8871 alternative: one PH pin per motor (replaces IN2), no STBY —
 * see motor_control.c comments. */

/* ---------------- Diagnostics LED (on-board LD2) ---------------- */
#define LED_GPIO_PORT  GPIOA
#define LED_GPIO_PIN   GPIO_PIN_5

#endif /* PIN_CONFIG_H */
