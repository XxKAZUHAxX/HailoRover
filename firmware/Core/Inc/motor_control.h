/**
 * Motor Control — TB6612FNG / DRV8871 dual H-bridge interface
 *
 * Differential drive: two motors, each with direction + PWM.
 * PWM frequency: 20 kHz (above audible range).
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <stdint.h>

void motor_init(void);
void motor_set_left(int8_t speed);   /* -100 to 100 */
void motor_set_right(int8_t speed);  /* -100 to 100 */
void motor_stop(void);               /* Coast */
void motor_brake(void);              /* Active brake */

#endif /* MOTOR_CONTROL_H */
