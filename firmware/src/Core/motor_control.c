/**
 * motor_control.c — DRV8871 dual H-bridge via TIM2 PWM + direction GPIOs.
 *
 * Wiring (Nucleo-F446RE defaults, see pin_config.h):
 *   Left : PWM PA0 (TIM2_CH1) → IN1,   dir PC0 → IN2
 *   Right: PWM PA1 (TIM2_CH2) → IN1,   dir PC2 → IN2
 *   VMOT = motor supply (12 V here), VCC = 3.3 V logic.
 *   DRV8871 has NO standby pin.
 *
 * DRV8871 truth table (IN1 = PWM pin, IN2 = direction GPIO):
 *   forward: IN2 LOW,  duty = speed%        (IN1 PWM)
 *   reverse: IN2 HIGH, duty = (100-speed)%  (IN1 PWM; 0% duty = full reverse)
 *   coast:   IN2 HIGH, duty = 100%          (INs HIGH-HIGH = coast)
 *   brake:   IN2 LOW,  duty = 0%            (INs LOW-LOW = short brake)
 * NOTE: this is the OPPOSITE of the TB6612FNG (which coasts on LOW-LOW and
 * brakes on HIGH-HIGH) — do not mix wiring semantics between the two.
 *
 * PWM: 20 kHz (ARR 4499 at the 90 MHz APB1 timer clock).
 */

#include "stm32f4xx_hal.h"

#include "motor_control.h"
#include "pin_config.h"

static TIM_HandleTypeDef htim2;

static uint16_t scale_duty(uint8_t speed)
{
    uint32_t d;

    /* speed 0..100 -> 0..PERIOD */
    d = ((uint32_t)speed * (uint32_t)(MOTOR_PWM_PERIOD + 1UL)) / 100UL;
    if (d > (uint32_t)MOTOR_PWM_PERIOD) {
        d = (uint32_t)MOTOR_PWM_PERIOD;
    }
    return (uint16_t)d;
}

static void apply_channel(GPIO_TypeDef *dir_port, uint16_t dir_pin,
                          uint32_t channel, int8_t speed)
{
    uint16_t duty;

    if (speed > 0) {
        HAL_GPIO_WritePin(dir_port, dir_pin, GPIO_PIN_RESET);   /* forward */
        duty = scale_duty((uint8_t)speed);
    } else if (speed < 0) {
        HAL_GPIO_WritePin(dir_port, dir_pin, GPIO_PIN_SET);     /* reverse */
        /* Inverted duty: 0% duty = full reverse, 100% = coast */
        duty = scale_duty((uint8_t)(100 - (uint8_t)(-speed)));
    } else {
        HAL_GPIO_WritePin(dir_port, dir_pin, GPIO_PIN_SET);     /* coast */
        duty = (uint16_t)MOTOR_PWM_PERIOD;                      /* IN1 HIGH */
    }
    __HAL_TIM_SET_COMPARE(&htim2, channel, duty);
}

void motor_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();

    /* Direction pins: drive HIGH first = coast for both motors */
    gpio.Pin = MOTOR_L_DIR_PIN | MOTOR_R_DIR_PIN;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_MEDIUM;
    HAL_GPIO_Init(GPIOC, &gpio);
    HAL_GPIO_WritePin(MOTOR_L_DIR_PORT, MOTOR_L_DIR_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR_R_DIR_PORT, MOTOR_R_DIR_PIN, GPIO_PIN_SET);

    /* PWM pins PA0/PA1, AF1 */
    gpio.Pin = MOTOR_PWM_LEFT_PIN | MOTOR_PWM_RIGHT_PIN;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    gpio.Alternate = MOTOR_PWM_GPIO_AF;
    HAL_GPIO_Init(MOTOR_PWM_GPIO_PORT, &gpio);

    htim2.Instance = MOTOR_TIM;
    htim2.Init.Prescaler = 0U;
    htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim2.Init.Period = (uint32_t)MOTOR_PWM_PERIOD;
    htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    HAL_TIM_PWM_Init(&htim2);

    TIM_OC_InitTypeDef oc = {0};
    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0U;   /* brake at init (INs LOW-LOW on DRV8871) */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;

    HAL_TIM_PWM_ConfigChannel(&htim2, &oc, MOTOR_PWM_LEFT_CHANNEL);
    HAL_TIM_PWM_ConfigChannel(&htim2, &oc, MOTOR_PWM_RIGHT_CHANNEL);
    HAL_TIM_PWM_Start(&htim2, MOTOR_PWM_LEFT_CHANNEL);
    HAL_TIM_PWM_Start(&htim2, MOTOR_PWM_RIGHT_CHANNEL);
}

void motor_set_left(int8_t speed)
{
    apply_channel(MOTOR_L_DIR_PORT, MOTOR_L_DIR_PIN, MOTOR_PWM_LEFT_CHANNEL, speed);
}

void motor_set_right(int8_t speed)
{
    apply_channel(MOTOR_R_DIR_PORT, MOTOR_R_DIR_PIN, MOTOR_PWM_RIGHT_CHANNEL, speed);
}

void motor_stop(void)
{
    /* Coast: INs HIGH-HIGH on DRV8871 */
    HAL_GPIO_WritePin(MOTOR_L_DIR_PORT, MOTOR_L_DIR_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR_R_DIR_PORT, MOTOR_R_DIR_PIN, GPIO_PIN_SET);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_LEFT_CHANNEL, (uint32_t)MOTOR_PWM_PERIOD);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_RIGHT_CHANNEL, (uint32_t)MOTOR_PWM_PERIOD);
}

void motor_brake(void)
{
    /* Short brake: INs LOW-LOW on DRV8871 */
    HAL_GPIO_WritePin(MOTOR_L_DIR_PORT, MOTOR_L_DIR_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(MOTOR_R_DIR_PORT, MOTOR_R_DIR_PIN, GPIO_PIN_RESET);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_LEFT_CHANNEL, 0U);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_RIGHT_CHANNEL, 0U);
}
