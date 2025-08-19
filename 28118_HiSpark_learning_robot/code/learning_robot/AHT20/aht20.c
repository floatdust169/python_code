#include "pinctrl.h"
#include "i2c.h"
#include "osal_debug.h"
#include "cmsis_os2.h"
#include "aht20.h"

#define AHT20_STARTUP_TIME (20 * 10)     // 上电启动时间
#define AHT20_CALIBRATION_TIME (40 * 10) // 初始化（校准）时间
#define AHT20_MEASURE_TIME (75 * 10)     // 测量时间

#define AHT20_DEVICE_ADDR 0x38
#define AHT20_READ_ADDR ((0x38 << 1) | 0x1)
#define AHT20_WRITE_ADDR ((0x38 << 1) | 0x0)

#define AHT20_CMD_CALIBRATION 0xBE 
#define AHT20_CMD_CALIBRATION_ARG0 0x08
#define AHT20_CMD_CALIBRATION_ARG1 0x00

#define AHT20_CMD_TRIGGER 0xAC // 触发测量命令
#define AHT20_CMD_TRIGGER_ARG0 0x33
#define AHT20_CMD_TRIGGER_ARG1 0x00

#define AHT20_CMD_RESET 0xBA // 软复位命令

#define AHT20_CMD_STATUS 0x71 // 获取状态命令

#define AHT20_STATUS_BUSY_SHIFT 7 
#define AHT20_STATUS_BUSY_MASK (0x1 << AHT20_STATUS_BUSY_SHIFT)

#define AHT20_STATUS_MODE_SHIFT 5 
#define AHT20_STATUS_MODE_MASK (0x3 << AHT20_STATUS_MODE_SHIFT)

#define AHT20_STATUS_CALI_SHIFT 3                               
#define AHT20_STATUS_CALI_MASK (0x1 << AHT20_STATUS_CALI_SHIFT) 

#define AHT20_STATUS_RESPONSE_MAX 6

#define AHT20_RESLUTION (1 << 20)

#define AHT20_MAX_RETRY 10
#define CONFIG_I2C_MASTER_BUS_ID 1
#define I2C_SLAVE1_ADDR 0x38

uint8_t aht20_status_busy(uint8_t status)
{
    return ((status & AHT20_STATUS_BUSY_MASK) >> (AHT20_STATUS_BUSY_SHIFT));
}

uint8_t aht20_status_mode(uint8_t status)
{
    return ((status & AHT20_STATUS_MODE_MASK) >> (AHT20_STATUS_MODE_SHIFT));
}

uint8_t aht20_status_cali(uint8_t status)
{
    return ((status & AHT20_STATUS_CALI_MASK) >> (AHT20_STATUS_CALI_SHIFT));
}

static uint32_t AHT20_Read(uint8_t *buffer, uint32_t buffLen)
{
    uint16_t dev_addr = AHT20_DEVICE_ADDR;
    i2c_data_t data = {0};
    data.receive_buf = buffer;
    data.receive_len = buffLen;
    uint32_t retval = uapi_i2c_master_read(CONFIG_I2C_MASTER_BUS_ID, dev_addr, &data);
    if (retval != 0) {
        printf("I2cRead() failed, %d!\n", retval);
        return retval;
    }
    return 0;
}

// 返回0表示正常状态
static uint32_t AHT20_Write(uint8_t *buffer, uint32_t buffLen)
{
    uint16_t dev_addr = AHT20_DEVICE_ADDR;
    i2c_data_t data = {0};
    data.send_buf = buffer;
    data.send_len = buffLen;
    uint32_t retval = uapi_i2c_master_write(CONFIG_I2C_MASTER_BUS_ID, dev_addr, &data);
    if (retval != 0) {
        printf("I2cWrite(%d) failed, %d!\n", buffer[0], retval);
        return retval;
    }
    return 0;
}

// 发送获取状态命令
static uint32_t AHT20_StatusCommand(void)
{
    uint8_t statusCmd[] = {AHT20_CMD_STATUS};
    return AHT20_Write(statusCmd, sizeof(statusCmd));
}

// 发送软复位命令
static uint32_t AHT20_ResetCommand(void)
{
    uint8_t resetCmd[] = {AHT20_CMD_RESET};
    return AHT20_Write(resetCmd, sizeof(resetCmd));
}

// 发送初始化校准命令
static uint32_t AHT20_CalibrateCommand(void)
{
    uint8_t clibrateCmd[] = {AHT20_CMD_CALIBRATION, AHT20_CMD_CALIBRATION_ARG0, AHT20_CMD_CALIBRATION_ARG1};
    return AHT20_Write(clibrateCmd, sizeof(clibrateCmd));
}

uint32_t AHT20_Calibrate(void)
{
    uint32_t retval = 0;
    uint8_t buffer[AHT20_STATUS_RESPONSE_MAX] = {AHT20_CMD_STATUS};
    memset_s(&buffer, sizeof(buffer), 0x0, sizeof(buffer));
    retval = AHT20_StatusCommand();
    if (retval != 0) {
        return retval;
    }

    retval = AHT20_Read(buffer, sizeof(buffer));
    if (retval != 0) {
        return retval;
    }

    if (aht20_status_busy(buffer[0]) || !aht20_status_cali(buffer[0])) {
        retval = AHT20_ResetCommand();
        if (retval != 0) {
            return retval;
        }
        osDelay(AHT20_STARTUP_TIME);
        retval = AHT20_CalibrateCommand();
        osDelay(AHT20_CALIBRATION_TIME);
        return retval;
    }
    return 0;
}

// 发送 触发测量 命令，开始测量 返回0表示正常状态
uint32_t AHT20_StartMeasure(void)
{
    uint8_t triggerCmd[] = {AHT20_CMD_TRIGGER, AHT20_CMD_TRIGGER_ARG0, AHT20_CMD_TRIGGER_ARG1};
    return AHT20_Write(triggerCmd, sizeof(triggerCmd));
}

// 接收测量结果，拼接转换为标准值
uint32_t AHT20_GetMeasureResult(float *temp, float *humi)
{
    uint32_t retval = 0, i = 0;
    if (temp == NULL || humi == NULL) {
        return 0;
    }

    uint8_t buffer[AHT20_STATUS_RESPONSE_MAX] = {0};
    memset_s(&buffer, sizeof(buffer), 0x0, sizeof(buffer));
    retval = AHT20_Read(buffer, sizeof(buffer));
    if (retval != 0) {
        return retval;
    }

    for (i = 0; aht20_status_busy(buffer[0]) && i < AHT20_MAX_RETRY; i++) {
        osDelay(10);
        retval = AHT20_Read(buffer, sizeof(buffer));
        if (retval != 0) {
            return retval;
        }
    }
    if (i >= AHT20_MAX_RETRY) {
        printf("AHT20 device always busy!\r\n");
        return 0;
    }

    uint32_t humiRaw = buffer[1];
    humiRaw = (humiRaw << 8) | buffer[2];
    humiRaw = (humiRaw << 4) | ((buffer[3] & 0xF0) >> 4); 
    *humi = humiRaw / (float)AHT20_RESLUTION * 100; 

    uint32_t tempRaw = buffer[3] & 0x0F;
    tempRaw = (tempRaw << 8) | buffer[4]; 
    tempRaw = (tempRaw << 8) | buffer[5];
    *temp = tempRaw / (float)AHT20_RESLUTION * 200 - 50; 
    return 0;
}