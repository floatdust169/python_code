#include "pinctrl.h"
#include "uart.h"
#include "osal_debug.h"
#include "soc_osal.h"
#include "app_init.h"
#include "string.h"
#include "cmsis_os2.h"
#include "uart_show.h"

osThreadId_t task1_ID; // 任务1 ID

#define DELAY_TIME_MS 1
#define UART_RECV_SIZE 23


/* 风扇:    包头1:0x55   包头2:0x02   Rx_Wind_Data[1]:0x01手动调节    Rx_Wind_Data[2]: 手动调节对应的占空比  包尾�?0x00*/
/* Wifi:    包头1:0x10   包头2:0x01/0x02    用户�?/密码      Rx_Wind_Data[1]:0x01/0x02 �?�?/手动调节    Rx_Wind_Data[2]: 手动调节对应的占空比  包尾�?0x00*/

/*  �?行修改部�?2 begin */
#define     Rx_Wind_Head               0x55
#define     Rx_Wind_Choose             0x02
#define     Rx_Wind_Tail               0x00

#define     Rx_Wifi_Head               0x10
#define     Rx_Wifi_User               0x01
#define     Rx_Wifi_Key                0x02
#define     Rx_Wifi_User_Tail          0xFF
#define     Rx_Wifi_Key_Tail           0xFF

#define     Memory_Delete_Head1        0x02
#define     Memory_Delete_Head2        0x03
#define     Memory_Delete_Tail         0xFF


/*  �?行修改部�?2 end   */


uint8_t uart_recv[UART_RECV_SIZE] = {0};//uart_recv
uint8_t Rx_Wind_Data[Rx_Length] = {0};
char Rx_Wifi_User_Data[Rx_Length] = {0};
char Rx_Wifi_Key_Data[Rx_Length] = {0};
char Rx_Memory_Delete_Data[Rx_Length] = {0};

// 组合后的字符串“delete:%s”
char delete[Rx_Length + 10];


#define UART_INT_MODE 1
#if (UART_INT_MODE)
static uint8_t uart_rx_flag = 0;
/*  �?行修改部�?1 begin */
static uint8_t uart_rx_WindState = 0;
static uint8_t uart_rx_Wifi_User_State = 0;
static uint8_t uart_rx_Wifi_Key_State = 0;
static uint8_t uart_rx_Memory_Delete_State = 0;

static uint8_t uart_rx_Wind_dataFlag = 0;
static uint8_t uart_rx_Wifi_User_dataFlag = 0;
static uint8_t uart_rx_Wifi_Key_dataFlag = 0;
static uint8_t uart_rx_Memory_Delete_dataFlag = 0;

/*  �?行修改部�?1 end   */
#endif
uart_buffer_config_t g_app_uart_buffer_config = {.rx_buffer = uart_recv, .rx_buffer_size = UART_RECV_SIZE};

void uart_gpio_init(void)
{
    uapi_pin_set_mode(GPIO_07, PIN_MODE_2); //Rx
    uapi_pin_set_mode(GPIO_08, PIN_MODE_2); //Tx
}

void uart_init_config(void)
{
    uart_attr_t attr = {
        .baud_rate = 115200, .data_bits = UART_DATA_BIT_8, .stop_bits = UART_STOP_BIT_1, .parity = UART_PARITY_NONE};

    uart_pin_config_t pin_config = {.tx_pin = S_MGPIO0, .rx_pin = S_MGPIO1, .cts_pin = PIN_NONE, .rts_pin = PIN_NONE};
    uapi_uart_deinit(UART_BUS_2);
    int ret = uapi_uart_init(UART_BUS_2, &pin_config, &attr, NULL, &g_app_uart_buffer_config);
    if (ret != 0) {
        printf("uart init failed ret = %02x\n", ret);
    }
    // printf("2025");
    // printf("7");
    // printf("3");
    // printf("14");
    // printf("04");
}

#if (UART_INT_MODE)
void uart_read_handler(const void *buffer, uint16_t length, bool error)
{
    unused(error);
    if (buffer == NULL || length == 0) {
        return;
    }
    if (memcpy_s(uart_recv, length, buffer, length) != EOK) {
        return;
    }
    //for(int i = 0 ;i < length;i++)
    //{
        //printf("uart_recv[%d] = %c",i,uart_recv[i]);
    //}
    uart_rx_flag = 1;
}
#endif

void *uart_task(const char *arg)
{
    unused(arg);
    uart_gpio_init();
    uart_init_config();

#if (UART_INT_MODE)
    // 注册串口回调函数
    if (uapi_uart_register_rx_callback(UART_BUS_2, UART_RX_CONDITION_MASK_IDLE, Rx_Length, uart_read_handler) == ERRCODE_SUCC) 
    {

    }
#endif

    while (1) {
#if (UART_INT_MODE)
        while (!uart_rx_flag) {
            osDelay(DELAY_TIME_MS);
        }
        /*  �?行修改部�?3 begin   */
        for(int i = 0;i < Rx_Length;i++)
        {
            /* 风扇 */
            if(uart_rx_WindState == 0)
            {
                if(uart_recv[i] == Rx_Wind_Head)
                {
                    uart_rx_WindState = 1;
                }
                //printf("uart_rx_WindState == 0:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_WindState == 1)
            {
                if(uart_recv[i] == Rx_Wind_Choose)
                {
                    uart_rx_WindState = 2;
                }
                else
                {
                    uart_rx_WindState = 0;
                }
                //printf("uart_rx_WindState == 1:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_WindState == 2)
            {
                static int j = 0;
                if(uart_recv[i] == Rx_Wind_Tail)
                {
                    j = 0;
                    uart_rx_WindState = 0;
                    uart_rx_Wind_dataFlag = 1;
                }
                else
                {
                    Rx_Wind_Data[j++] = uart_recv[i];
                    printf("Rx_Wind_Data[%d] = %c  \n",j - 1,Rx_Wind_Data[j - 1]);
                }
                
            }
            /* Wifi_User */
            if(uart_rx_Wifi_User_State == 0)
            {
                if(uart_recv[i] == Rx_Wifi_Head)
                {
                    uart_rx_Wifi_User_State = 1;
                }
                //printf("uart_rx_Wifi_User_State == 0:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Wifi_User_State == 1)
            {
                if(uart_recv[i] == Rx_Wifi_User)
                {
                    uart_rx_Wifi_User_State = 2;
                }
                else
                {
                    uart_rx_Wifi_User_State = 0;
                }
                //printf("uart_rx_Wifi_User_State == 1:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Wifi_User_State == 2)
            {
                static int j = 0;
                if(uart_recv[i] == Rx_Wifi_User_Tail)
                {
                    j = 0;
                    uart_rx_Wifi_User_State = 0;
                    uart_rx_Wifi_User_dataFlag = 1;
                }
                else
                {
                    Rx_Wifi_User_Data[j++] = uart_recv[i];
                    printf("Rx_Wifi_User_Data[%d] = %c  \n",j - 1,Rx_Wifi_User_Data[j - 1]);
                }
            }
            /* Wifi_Key */
            if(uart_rx_Wifi_Key_State == 0)
            {
                if(uart_recv[i] == Rx_Wifi_Head)
                {
                    uart_rx_Wifi_Key_State = 1;
                }
                //printf("uart_rx_Wifi_Key_State == 0:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Wifi_Key_State == 1)
            {
                if(uart_recv[i] == Rx_Wifi_Key)
                {
                    uart_rx_Wifi_Key_State = 2;
                }
                else
                {
                    uart_rx_Wifi_Key_State = 0;
                }
                //printf("uart_rx_Wifi_Key_State == 1:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Wifi_Key_State == 2)
            {
                static int j = 0;
                if(uart_recv[i] == Rx_Wifi_Key_Tail)
                {
                    j = 0;
                    uart_rx_Wifi_Key_State = 0;
                    uart_rx_Wifi_Key_dataFlag = 1;
                }
                else
                {
                    Rx_Wifi_Key_Data[j++] = uart_recv[i];
                    printf("Rx_Wifi_Key_Data[%d] = %c  \n",j - 1,Rx_Wifi_Key_Data[j - 1]);
                }
                
            }
            /* Memory Delete */
            if(uart_rx_Memory_Delete_State == 0)
            {
                if(uart_recv[i] == Memory_Delete_Head1)
                {
                    uart_rx_Memory_Delete_State = 1;
                }
                //printf("uart_rx_Wifi_Key_State == 0:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Memory_Delete_State == 1)
            {
                if(uart_recv[i] == Memory_Delete_Head2)
                {
                    uart_rx_Memory_Delete_State = 2;
                }
                else
                {
                    uart_rx_Memory_Delete_State = 0;
                }
                //printf("uart_rx_Wifi_Key_State == 1:  %d  \n",uart_recv[i]);
            }
            else if(uart_rx_Memory_Delete_State == 2)
            {
                static int j = 0;
                if(uart_recv[i] == Memory_Delete_Tail)
                {
                    j = 0;
                    uart_rx_Memory_Delete_State = 0;
                    uart_rx_Memory_Delete_dataFlag = 1;
                }
                else
                {
                    Rx_Memory_Delete_Data[j++] = uart_recv[i];
                    printf("Rx_Memory_Delete_Data[%d] = %c  \n",j - 1,Rx_Memory_Delete_Data[j - 1]);
                }
                
            }
        }
        memset(uart_recv, 0, UART_RECV_SIZE);
        uart_rx_flag = 0;

        // 删除任务回传
        if(strlen(Rx_Memory_Delete_Data) != 0 && sock_fd >= 0)
        {
            sprintf(delete,"delete:%s",Rx_Memory_Delete_Data);
            memset(Rx_Memory_Delete_Data, 0,Rx_Length);
            lwip_send(sock_fd, delete, strlen(delete), 0);  
            memset(delete, 0, Rx_Length + 10);  
        }
        
        // if(uart_recv[0] == Rx_Wifi_Head&&uart_recv[1] == Rx_Wifi_User&&uart_recv[21] == 0x00)//Wifi用户名的包头和包尾�?�应，则为用户名
        // {
        //     uart_rx_Wifi_User_dataFlag = 1;
        //     uart_rx_flag = 0;
        //     for(int i = 0;i < 5;i++)
        //     {
        //         printf("%d  ",uart_recv[i]);
        //     }
        //     printf("Wifi_User_Flag = %d  ",uart_rx_Wifi_User_dataFlag);
        // }
        // else
        // {
        //     memset(uart_recv, 0, UART_RECV_SIZE);
        // }
        /*  �?行修改部�?3 end   */

        // printf("%d  \n",uart_recv[0]);
        // for(int i = 0;i < Rx_WindLength;i++)
        // {
        //     printf("%d  ",Rx_DataArr[i]);
        // }
        
        // printf("uart int rx = [%s]\n", uart_recv);
        // printf("uart_rx_flag = %d",uart_rx_flag);
        // for(int i = 0;i < 3;i++)
        // {
        //     printf("uart_recv[%d] = %d\n",i,uart_recv[i]);
        // }
        //memset(uart_recv, 0, UART_RECV_SIZE);
#else
        if (uapi_uart_read(UART_BUS_0, uart_recv, UART_RECV_SIZE, 0)) {
            printf("uart poll rx = ");
            uapi_uart_write(UART_BUS_0, uart_recv, UART_RECV_SIZE, 0);
        }
#endif
    }
    return NULL;
}

void uart_entry(void)
{
    printf("Enter uart_entry()!\r\n");

    osThreadAttr_t attr;
    attr.name = "UartTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 0x1000;
    attr.priority = osPriorityNormal;

    task1_ID = osThreadNew((osThreadFunc_t)uart_task, NULL, &attr);
    if (task1_ID != NULL) {
        printf("ID = %d, Create task1_ID is OK!\r\n", task1_ID);
    }
}