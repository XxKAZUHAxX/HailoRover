/**
 * FreeRTOS kernel configuration — HailoRover motor controller.
 *
 * Policy: static allocation ONLY (configSUPPORT_DYNAMIC_ALLOCATION 0, no heap
 * file compiled) — MISRA-inspired: no malloc exists at all, task stacks live
 * in named static arrays in .bss.
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H

/* --------------------------------------------------------------------------
 * Scheduling
 * ------------------------------------------------------------------------*/
#define configUSE_PREEMPTION                    1
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 1
#define configUSE_TICKLESS_IDLE                 0
#define configCPU_CLOCK_HZ                      ( 180000000UL )
#define configTICK_RATE_HZ                      ( 1000 )
#define configMAX_PRIORITIES                    ( 4 )
#define configMINIMAL_STACK_SIZE                ( 128 )
#define configMAX_TASK_NAME_LEN                 ( 12 )
#define configUSE_16_BIT_TICKS                  0
#define configIDLE_SHOULD_YIELD                 1
#define configUSE_TIME_SLICING                  1

/* --------------------------------------------------------------------------
 * Features we don't use (kept off to keep the footprint honest)
 * ------------------------------------------------------------------------*/
#define configUSE_MUTEXES                       0
#define configUSE_RECURSIVE_MUTEXES             0
#define configUSE_COUNTING_SEMAPHORES           0
#define configUSE_TIMERS                        0
#define configUSE_TASK_NOTIFICATIONS            0
#define configUSE_MALLOC_FAILED_HOOK            0
#define configUSE_IDLE_HOOK                     0
#define configUSE_TICK_HOOK                     0

/* --------------------------------------------------------------------------
 * Allocation: static only
 * ------------------------------------------------------------------------*/
#define configSUPPORT_STATIC_ALLOCATION         1
#define configSUPPORT_DYNAMIC_ALLOCATION        0
#define configTOTAL_HEAP_SIZE                   ( 0 )
#define configQUEUE_REGISTRY_SIZE               0

/* --------------------------------------------------------------------------
 * Diagnostics
 * ------------------------------------------------------------------------*/
#define configCHECK_FOR_STACK_OVERFLOW          2
#define configUSE_STATS_FORMATTING_FUNCTIONS    0
#define configRECORD_STACK_HIGH_ADDRESS         0

#define configASSERT( x )                       do { if( ( x ) == 0 ) { taskDISABLE_INTERRUPTS(); for( ;; ); } } while( 0 )

/* --------------------------------------------------------------------------
 * Interrupt priorities (STM32F4: 4 priority bits)
 * ------------------------------------------------------------------------*/
#define configPRIO_BITS                         4
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY          15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY     5   /* USART6 IRQ runs here */
#define configKERNEL_INTERRUPT_PRIORITY         ( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << ( 8 - configPRIO_BITS ) )
#define configMAX_SYSCALL_INTERRUPT_PRIORITY    ( configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << ( 8 - configPRIO_BITS ) )

/* --------------------------------------------------------------------------
 * Hooks (implemented in app_tasks.c)
 * ------------------------------------------------------------------------*/
#define configUSE_NEWLIB_REENTRANT              0
#define configENABLE_BACKWARD_COMPATIBILITY     0
#define configUSE_POSIX_ERRNO                   0

#define INCLUDE_vTaskDelayUntil                 1
#define INCLUDE_vTaskDelay                      1
#define INCLUDE_xTaskGetSchedulerState          0
#define INCLUDE_uxTaskGetStackHighWaterMark     1
#define INCLUDE_xTaskGetIdleTaskHandle          0
#define INCLUDE_pxTaskGetStackStart             0

/* FPU: hardware floating point in tasks (Cortex-M4F) */
#define configENABLE_FPU                        1
#define configENABLE_TRUSTZONE                  0

#endif /* FREERTOS_CONFIG_H */
