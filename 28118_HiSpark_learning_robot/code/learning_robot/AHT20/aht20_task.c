#include "pinctrl.h"
#include "i2c.h"
#include "osal_debug.h"
#include "soc_osal.h"
#include "aht20.h"
#include "app_init.h"

#define AHT20_SCL_PIN 15
#define AHT20_SDA_PIN 16
#define I2C_MASTER_ADDR 0x0
#define I2C_SLAVE1_ADDR 0x38
#define I2C_SET_BANDRATE 400000
#define I2C_TASK_STACK_SIZE 0x2000
#define I2C_TASK_PRIO 24

float temp = 0.0f;
float humi = 0.0f;

void AHT20Task(void)
{
    uint32_t retval = 0;

    uint32_t baudrate = I2C_SET_BANDRATE;
    uint32_t hscode = I2C_MASTER_ADDR;
    uapi_pin_set_mode(AHT20_SCL_PIN, PIN_MODE_2);
    uapi_pin_set_mode(AHT20_SDA_PIN, PIN_MODE_2);
    uapi_i2c_master_init(1, baudrate, hscode);

    while (AHT20_Calibrate() != 0) {
        printf("AHT20 sensor init failed!\r\n");
        osal_mdelay(100);
    }

    while (1) {
        retval = AHT20_StartMeasure();
        printf("AHT20_StartMeasure: %d\r\n", retval);

        retval = AHT20_GetMeasureResult(&temp, &humi);
        if (retval != 0) {
            printf("get humidity data failed!\r\n");
        }
        
        osal_mdelay(1000);
    }
}

void AHT20TASK_entry(void)
{
    osal_task *task_handle = NULL;
    osal_kthread_lock();
    task_handle = osal_kthread_create((osal_kthread_handler)AHT20Task, 0, "AHT20Task", I2C_TASK_STACK_SIZE);
    if (task_handle != NULL) {
        osal_kthread_set_priority(task_handle, I2C_TASK_PRIO);
        osal_kfree(task_handle);
    }
    osal_kthread_unlock();
}