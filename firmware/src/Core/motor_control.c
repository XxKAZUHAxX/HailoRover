/**
 * motor_control.c — TB6612FNG dual H-bridge via TIM2 PWM + direction GPIOs.
 *
 * Wiring (Nucleo-F446RE defaults, see pin_config.h):
 *   PWMA ← PA0 (TIM2_CH1)   PWMB ← PA1 (TIM2_CH2)
 *   AIN1 ← PC0  AIN2 ← PC1  BIN1 ← PC2  BIN2 ← PC3   STBY ← PC4
 *   VMOT = 12 V motor supply, VCC = 3.3 V logic. STBY stays HIGH after init.
 *
 * TB6612FNG truth table (per channel): IN1/IN2 LOW-LOW = coast, HIGH-HIGH =
 * short brake, HIGH-LOW / LOW-HIGH = CW/CCW with PWM on the enabled input.
 *
 * DRV8871 alternative (documented, not wired): one PH pin per motor replaces
 * IN2 (PH LOW = reverse), EN ties to the PWM pin, no STBY pin.
 *
 * PWM: 20 kHz (ARR 4499 at the 90 MHz APB1 timer clock).
 */

#include "stm32f4xx_hal.h"

#include "motor_control.h"
#include "pin_config.h"

static TIM_HandleTypeDef htim2;

/* Direction pin bundles */
typedef struct {
    GPIO_TypeDef *port1;
    uint16_t      pin1;
    GPIO_TypeDef *port2;
    uint16_t      pin2;
} motor_dir_pins_t;

static const motor_dir_pins_t dir_left  = { MOTOR_L_IN1_PORT, MOTOR_L_IN1_PIN, MOTOR_L_IN2_PORT, MOTOR_L_IN2_PIN };
static const motor_dir_pins_t dir_right = { MOTOR_R_IN1_PORT, MOTOR_R_IN1_PIN, MOTOR_R_IN2_PORT, MOTOR_R_IN2_PIN };

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

static void set_dir(const motor_dir_pins_t *pins, uint8_t in1, uint8_t in2)
{
    HAL_GPIO_WritePin(pins->port1, pins->pin1, (in1 != 0U) ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(pins->port2, pins->pin2, (in2 != 0U) ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static void apply_channel(const motor_dir_pins_t *dir, uint32_t channel, int8_t speed)
{
    uint16_t duty;

    if (speed > 0) {
        set_dir(dir, 1U, 0U);                    /* forward */
        duty = scale_duty((uint8_t)speed);
    } else if (speed < 0) {
        set_dir(dir, 0U, 1U);                    /* reverse */
        duty = scale_duty((uint8_t)(-speed));
    } else {
        set_dir(dir, 0U, 0U);                    /* coast */
        duty = 0U;
    }
    __HAL_TIM_SET_COMPARE(&htim2, channel, duty);
}

void motor_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_TIM2_CLK_ENABLE();

    /* Direction pins: outputs LOW first (coast), before STBY goes HIGH */
    gpio.Pin = MOTOR_L_IN1_PIN | MOTOR_L_IN2_PIN | MOTOR_R_IN1_PIN | MOTOR_R_IN2_PIN | MOTOR_STBY_PIN;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_MEDIUM;
    HAL_GPIO_Init(GPIOC, &gpio);

    set_dir(&dir_left, 0U, 0U);
    set_dir(&dir_right, 0U, 0U);
    HAL_GPIO_WritePin(MOTOR_STBY_PORT, MOTOR_STBY_PIN, GPIO_PIN_SET);   /* STBY stays HIGH */

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
    oc.Pulse = 0U;   /* coast at init */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;

    HAL_TIM_PWM_ConfigChannel(&htim2, &oc, MOTOR_PWM_LEFT_CHANNEL);
    HAL_TIM_PWM_ConfigChannel(&htim2, &oc, MOTOR_PWM_RIGHT_CHANNEL);
    HAL_TIM_PWM_Start(&htim2, MOTOR_PWM_LEFT_CHANNEL);
    HAL_TIM_PWM_Start(&htim2, MOTOR_PWM_RIGHT_CHANNEL);
}

void motor_set_left(int8_t speed)
{
    apply_channel(&dir_left, MOTOR_PWM_LEFT_CHANNEL, speed);
}

void motor_set_right(int8_t speed)
{
    apply_channel(&dir_right, MOTOR_PWM_RIGHT_CHANNEL, speed);
}

void motor_stop(void)
{
    /* Coast: both INs low, PWM 0 */
    set_dir(&dir_left, 0U, 0U);
    set_dir(&dir_right, 0U, 0U);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_LEFT_CHANNEL, 0U);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_RIGHT_CHANNEL, 0U);
}

void motor_brake(void)
{
    /* Active short-brake: both INs high, PWM 0 */
    set_dir(&dir_left, 1U, 1U);
    set_dir(&dir_right, 1U, 1U);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_LEFT_CHANNEL, 0U);
    __HAL_TIM_SET_COMPARE(&htim2, MOTOR_PWM_RIGHT_CHANNEL, 0U);
}
