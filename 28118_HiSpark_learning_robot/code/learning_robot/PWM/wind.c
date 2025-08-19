#include "pinctrl.h"
#include "pwm.h"
#include "tcxo.h"
#include "soc_osal.h"
#include "app_init.h"
#include "../UART/uart_show.h"

#define PWM_CHANNEL 1
#define PWM_GROUP_ID 1
#define TEST_TCXO_DELAY_1000MS 1000

#define PWM_TASK_PRIO 24
#define PWM_TASK_STACK_SIZE 0x2000
#define CONFIG_PWM_PIN 23
#define CONFIG_PWM_PIN_MODE 1

void pwm_task(const char *arg)
{
    UNUSED(arg);
    //int change_state = 0;
    //int timer = 0;

    uapi_pin_set_mode(GPIO_01, HAL_PIO_FUNC_GPIO);
    uapi_gpio_set_dir(GPIO_01, GPIO_DIRECTION_OUTPUT);
    uapi_gpio_set_val(GPIO_01, GPIO_LEVEL_LOW);
    /*
    pwm_config_t cfg_no_repeat = {10000000,
                                  0,     // 高电平持续tick 时间 = tick * (1/32000000)
                                  0,     // 相位偏移位
                                  1,     // 发多少个波形
                                  true}; // 是否循环
    
    uapi_pin_set_mode(CONFIG_PWM_PIN, CONFIG_PWM_PIN_MODE);
    uapi_pin_set_ds(CONFIG_PWM_PIN, PIN_DS_MAX);
    uapi_pwm_init();
    osal_msleep(1000);

    uint8_t channel_id = PWM_CHANNEL;
    uapi_pwm_set_group(PWM_GROUP_ID, &channel_id, 1);
    uapi_pwm_open(PWM_CHANNEL, &cfg_no_repeat);
    uapi_pwm_start_group(1);
    

    if(uapi_pwm_start(PWM_GROUP_ID) == ERRCODE_SUCC)
    {
        printf("pwm%d start success",PWM_CHANNEL);
    }
    else
    {
        printf("pwm%d start Failed",PWM_CHANNEL);
    }
    */
    while (1)
    {
        //printf("0:%d 1:%d\n",Rx_Wind_Data[0],Rx_Wind_Data[1]);
        if(Rx_Wind_Data[0] == 1)//打开
        {
            if(Rx_Wind_Data[1] == 33)
            {
                // cfg_no_repeat.low_time = 2680; 
                // cfg_no_repeat.high_time = 1320; 
                // cfg_no_repeat.offset_time = 0; 
                // cfg_no_repeat.cycles = 1; 
                // cfg_no_repeat.repeat = TRUE; 
                // uapi_pwm_open(PWM_CHANNEL, &cfg_no_repeat);
                // uapi_pwm_set_group(PWM_GROUP_ID, &channel_id, 1);
                // uapi_pwm_start_group(1);

                // printf("33%%\n");
            }
            else if(Rx_Wind_Data[1] == 66)
            {
                // cfg_no_repeat.low_time = 1360; 
                // cfg_no_repeat.high_time = 2640; 
                // cfg_no_repeat.offset_time = 0; 
                // cfg_no_repeat.cycles = 1; 
                // cfg_no_repeat.repeat = TRUE; 
                // uapi_pwm_open(PWM_CHANNEL, &cfg_no_repeat);
                // uapi_pwm_set_group(PWM_GROUP_ID, &channel_id, 1);
                // uapi_pwm_start_group(1);

                // printf("66%%\n");
            }
            else if(Rx_Wind_Data[1] == 100)
            {
                // if(change_state == 0)
                // {
                //     cfg_no_repeat.low_time = 0; 
                //     cfg_no_repeat.high_time = 4000; 
                //     cfg_no_repeat.offset_time = 0; 
                //     cfg_no_repeat.cycles = 1; 
                //     cfg_no_repeat.repeat = TRUE; 
                //     uapi_pwm_open(PWM_CHANNEL, &cfg_no_repeat);
                //     uapi_pwm_set_group(PWM_GROUP_ID, &channel_id, 1);
                //     uapi_pwm_start_group(1);

                //     change_state = 1;
                // }

                printf("100%%\n");

                uapi_gpio_set_val(GPIO_01, GPIO_LEVEL_HIGH);
            }
        }
        else if(Rx_Wind_Data[0] == 0xFF)//关闭
        {
            uapi_gpio_set_val(GPIO_01, GPIO_LEVEL_LOW);
            
            //uapi_pwm_close(PWM_CHANNEL);

            printf("0%%\n");
        }

        osal_msleep(200);
    }
}

void pwm_entry(void)
{
    osal_task *task_handle = NULL;
    osal_kthread_lock();
    task_handle = osal_kthread_create((osal_kthread_handler)pwm_task, 0, "PwmTask", PWM_TASK_STACK_SIZE);
    if (task_handle != NULL) {
        osal_kthread_set_priority(task_handle, PWM_TASK_PRIO);
        osal_kfree(task_handle);
    }
    osal_kthread_unlock();
}