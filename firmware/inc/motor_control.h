/**
 * Motor Control — DRV8871 dual H-bridge interface
 *
 * Differential drive: two motors, each with a PWM input (IN1) and a
 * direction GPIO (IN2). PWM frequency: 20 kHz (above audible range).
 * Coast = INs HIGH-HIGH, brake = INs LOW-LOW (see motor_control.c).
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <stdint.h>

/* Safety watchdog: if no DRIVE command arrives within this window, the motor
 * task coasts both motors (single-writer — handled inside motor_task). */
#define WATCHDOG_COAST_TIMEOUT_MS  500U

void motor_init(void);
void motor_set_left(int8_t speed);   /* -100 to 100 */
void motor_set_right(int8_t speed);  /* -100 to 100 */
void motor_stop(void);               /* Coast */
void motor_brake(void);              /* Active brake */

#endif /* MOTOR_CONTROL_H */
