#include "wifista.h"
#include "lwip/sockets.h"

#include "lwip/opt.h"
#include "lwip/netifapi.h"
#include "lwip/netif.h"
#include "lwip/netifapi.h"
#include "wifi_hotspot.h"
#include "wifi_hotspot_config.h"
#include "td_base.h"
#include "td_type.h"
#include "stdlib.h"
#include "string.h"
#include "uart.h"
#include "cmsis_os2.h"
#include "app_init.h"
#include "soc_osal.h"

#include "uart.h"

#define WIFI_IFNAME_MAX_SIZE 16
#define WIFI_MAX_SSID_LEN 33
#define WIFI_SCAN_AP_LIMIT 64
#define WIFI_MAC_LEN 6
#define WIFI_STA_SAMPLE_LOG "[WIFI_STA]"
#define WIFI_NOT_AVALLIABLE 0
#define WIFI_AVALIABE 1
#define WIFI_GET_IP_MAX_COUNT 300

#define WIFI_TASK_PRIO (osPriority_t)(24)
#define WIFI_TASK_DURATION_MS 2000
#define WIFI_TASK_STACK_SIZE 0x2000

// 配置连接的wifi热点信息
#define WIFI_TARGET "XFC2025"
#define WIFI_TARGET_PASSWORD "XFC20041218"
// 配置云服务器信息
#define CLOUD_SERVER_IP "152.136.167.211"
#define USED_TCP_SOCKET_PORT 5000

static td_void wifi_scan_state_changed(td_s32 state, td_s32 size);
static td_void wifi_connection_changed(td_s32 state, const wifi_linked_info_stru *info, td_s32 reason_code);
int sta_sample_init(void *param);

// 作用域为整个工程
char sys_time[15];    //YYYYMMDDHHMMSS
char task[150];       //*task1@*task2@*task@
char envoronment[20]; //T:24.56H:70.03

int sock_fd;       //创建的套接字

// 系统使用的wifi信息
//td_char expected_ssid[] = WIFI_TARGET;
//td_char key[] = WIFI_TARGET_PASSWORD;
td_char expected_ssid[30] = {0};
td_char key[30] = {0};

void tcp_client_task(void);
uint8_t connect_to_server_flag = 0;

wifi_event_stru wifi_event_cb = {
    .wifi_event_connection_changed = wifi_connection_changed,
    .wifi_event_scan_state_changed = wifi_scan_state_changed,
};

enum {
    WIFI_STA_SAMPLE_INIT = 0,     /* 0:初始化 */
    WIFI_STA_SAMPLE_SCANING,      /* 1:扫描中 */
    WIFI_STA_SAMPLE_SCAN_DONE,    /* 2:扫描完成 */
    WIFI_STA_SAMPLE_FOUND_TARGET, /* 3:匹配到目标AP */
    WIFI_STA_SAMPLE_CONNECTING,   /* 4:连接 */
    WIFI_STA_SAMPLE_CONNECT_DONE, /* 5:关联成功 */
    WIFI_STA_SAMPLE_GET_IP,       /* 6:获取IP */
} wifi_state_enum;

static td_u8 g_wifi_state = WIFI_STA_SAMPLE_INIT;

/*****************************************************************************
  STA 扫描状态变化回调
*****************************************************************************/
static td_void wifi_scan_state_changed(td_s32 state, td_s32 size)
{
    UNUSED(state);
    UNUSED(size);
    PRINT("%s::Scan done!.\r\n", WIFI_STA_SAMPLE_LOG);
    g_wifi_state = WIFI_STA_SAMPLE_SCAN_DONE;
    return;
}

/*****************************************************************************
  STA 关联事件回调函数
*****************************************************************************/
static td_void wifi_connection_changed(td_s32 state, const wifi_linked_info_stru *info, td_s32 reason_code)
{
    UNUSED(info);
    UNUSED(reason_code);

    if (state == WIFI_NOT_AVALLIABLE) {
        PRINT("%s::Connect fail!. try agin !\r\n", WIFI_STA_SAMPLE_LOG);
        if(sock_fd >= 0)
            sock_fd = -1;
        g_wifi_state = WIFI_STA_SAMPLE_INIT;
    } else {
        PRINT("%s::Connect succ!.\r\n", WIFI_STA_SAMPLE_LOG);
        g_wifi_state = WIFI_STA_SAMPLE_CONNECT_DONE;
    }
}

/*****************************************************************************
  STA 匹配目标AP 成功返回0 否则返回-1
*****************************************************************************/
td_s32 example_get_match_network(wifi_sta_config_stru *expected_bss)
{
    td_s32 ret;
    td_u32 num = 64;

    td_bool find_ap = TD_FALSE;
    td_u8 bss_index;

    td_u32 scan_len = sizeof(wifi_scan_info_stru) * WIFI_SCAN_AP_LIMIT;
    wifi_scan_info_stru *result = osal_kmalloc(scan_len, OSAL_GFP_ATOMIC);
    // 接收到全非零字符
    printf("\n\nuser:%s len:%d r:%d",Rx_Wifi_User_Data, strlen(Rx_Wifi_User_Data), strcmp(Rx_Wifi_User_Data,"cyber0123"));
    printf("code:%s len:%d r:%d\n\n",Rx_Wifi_Key_Data, strlen(Rx_Wifi_User_Data), strcmp(Rx_Wifi_Key_Data, "hust1234"));
    if(strlen(Rx_Wifi_Key_Data) == 0 || strlen(Rx_Wifi_User_Data) == 0)
    {
        return -1;
        printf("WIFI MESSAGE ERROR!\n");
    }
    else
    {
        strcpy(expected_ssid, Rx_Wifi_User_Data);
        strcpy(key, Rx_Wifi_Key_Data);
    }

    if (result == TD_NULL) {
        return -1;
    }
    memset_s(result, scan_len, 0, scan_len);
    ret = wifi_sta_get_scan_info(result, &num);
    if (ret != 0) {
        osal_kfree(result);
        return -1;
    }
    /* 筛选扫描到的Wi-Fi网络，选择待连接的网络 */
    for (bss_index = 0; bss_index < num; bss_index++) {
        if (strlen(expected_ssid) == strlen(result[bss_index].ssid)) {
            if (memcmp(expected_ssid, result[bss_index].ssid, strlen(expected_ssid)) == 0) {
                find_ap = TD_TRUE;
                break;
            }
        }
    }

    if (find_ap == TD_FALSE) {
        osal_kfree(result);
        return -1;
    }
    /* 找到网络后复制网络信息和接入密码 */
    if (memcpy_s(expected_bss->ssid, WIFI_MAX_SSID_LEN, expected_ssid, strlen(expected_ssid)) != 0) {
        osal_kfree(result);
        return -1;
    }
    if (memcpy_s(expected_bss->bssid, WIFI_MAC_LEN, result[bss_index].bssid, WIFI_MAC_LEN) != 0) {
        osal_kfree(result);
        return -1;
    }
    expected_bss->security_type = result[bss_index].security_type;
    if (memcpy_s(expected_bss->pre_shared_key, WIFI_MAX_SSID_LEN, key, strlen(key)) != 0) {
        osal_kfree(result);
        return -1;
    }
    expected_bss->ip_type = 1; /* 1：IP类型为动态DHCP获取 */
    osal_kfree(result);
    return 0;
}

/*****************************************************************************
  STA 关联状态查询?
*****************************************************************************/
td_bool example_check_connect_status(td_void)
{
    td_u8 index;
    wifi_linked_info_stru wifi_status;
    /* 获取网络连接状态，共查�?5次，每�?�间�?500ms */
    for (index = 0; index < 5; index++) {
        (void)osDelay(50); /* 50: 延时500ms */
        memset_s(&wifi_status, sizeof(wifi_linked_info_stru), 0, sizeof(wifi_linked_info_stru));
        if (wifi_sta_get_ap_info(&wifi_status) != 0) {
            continue;
        }
        if (wifi_status.conn_state == 1) {
            return 0; /* 连接成功退出循�? */
        }
    }
    return -1;
}

/*****************************************************************************
  STA DHCP状态查询
*****************************************************************************/
td_bool example_check_dhcp_status(struct netif *netif_p, td_u32 *wait_count)
{
    if ((ip_addr_isany(&(netif_p->ip_addr)) == 0) && (*wait_count <= WIFI_GET_IP_MAX_COUNT)) {
        /* DHCP成功 */
        PRINT("%s::STA DHCP success.\r\n", WIFI_STA_SAMPLE_LOG);
        return 0;
    }

    if (*wait_count > WIFI_GET_IP_MAX_COUNT) {
        PRINT("%s::STA DHCP timeout, try again !.\r\n", WIFI_STA_SAMPLE_LOG);
        *wait_count = 0;
        g_wifi_state = WIFI_STA_SAMPLE_INIT;
    }
    return -1;
}

td_s32 example_sta_function(td_void)
{
    // 创建线程后 这个函数一直执行
    // 重新初始化wifi连接、STA等基础配置
    while (wifi_is_wifi_inited() == 0) 
    {
        (void)osDelay(10); // 等待后再判断状态
    }

    PRINT("%s::wifi init succ.\r\n", WIFI_STA_SAMPLE_LOG);
    td_char ifname[WIFI_IFNAME_MAX_SIZE + 1] = "wlan0";     /* 创建的STA接口 */
    wifi_sta_config_stru expected_bss = {0};                /* 连接请求信息 */
    struct netif *netif_p = TD_NULL;
    td_u32 wait_count = 0;

    /* 创建STA接口 */
    if (wifi_sta_enable() != 0) {
        return -1;
    }
    PRINT("%s::STA enable succ.\r\n", WIFI_STA_SAMPLE_LOG);

    do {
        (void)osDelay(1);
        if (g_wifi_state == WIFI_STA_SAMPLE_INIT) {
            PRINT("%s::Scan start!\r\n", WIFI_STA_SAMPLE_LOG);
            g_wifi_state = WIFI_STA_SAMPLE_SCANING;
            /* 启动STA扫描 */
            if (wifi_sta_scan() != 0) {
                g_wifi_state = WIFI_STA_SAMPLE_INIT;
                continue;
            }
        } else if (g_wifi_state == WIFI_STA_SAMPLE_SCAN_DONE) {
            /* 获取待连接的网络 */
            if (example_get_match_network(&expected_bss) != 0) {
                PRINT("%s::Do not find AP, try again !\r\n", WIFI_STA_SAMPLE_LOG);
                g_wifi_state = WIFI_STA_SAMPLE_INIT;
                continue;
            }
            g_wifi_state = WIFI_STA_SAMPLE_FOUND_TARGET;
        } else if (g_wifi_state == WIFI_STA_SAMPLE_FOUND_TARGET) {
            PRINT("%s::Connect start.\r\n", WIFI_STA_SAMPLE_LOG);
            g_wifi_state = WIFI_STA_SAMPLE_CONNECTING;

            /* 启动连接 */
            if (wifi_sta_connect(&expected_bss) != 0) {
                g_wifi_state = WIFI_STA_SAMPLE_INIT;
                continue;
            }
        } else if (g_wifi_state == WIFI_STA_SAMPLE_CONNECT_DONE) {
            PRINT("%s::DHCP start.\r\n", WIFI_STA_SAMPLE_LOG);
            g_wifi_state = WIFI_STA_SAMPLE_GET_IP;
            netif_p = netifapi_netif_find(ifname);
            if (netif_p == TD_NULL || netifapi_dhcp_start(netif_p) != 0) {
                PRINT("%s::find netif or start DHCP fail, try again !\r\n", WIFI_STA_SAMPLE_LOG);
                g_wifi_state = WIFI_STA_SAMPLE_INIT;
                continue;
            }
        } else if (g_wifi_state == WIFI_STA_SAMPLE_GET_IP) {
            if (example_check_dhcp_status(netif_p, &wait_count) == 0) {
                break;
            }
            wait_count++;
        }
    } while (1);

    // 启动wifi客户端
    PRINT("%s::Starting TCP client\n", WIFI_STA_SAMPLE_LOG);
    while(1)
    {
        tcp_client_task();
        break;
    }
    // 从上方的循环退出来即发生了异常
    wifi_sta_disable(); //释放STA资源 否则无法正常进行初始化

    return 0;
}

// 客户端任务
void tcp_client_task(void)
{
    int len = 0;
    int i, j = 0;
    struct sockaddr_in server_addr;

    char buffer[150];
    char message_to_uart[50] = {0};
    int alive_cnt = 0;
    int environment_cnt = 0;
    const char *gettime_command = "GetTime";
    const char *message = "Hello from device";

    while (1) {
        // 创建socket
        sock_fd = lwip_socket(AF_INET, SOCK_STREAM, 0);
        if (sock_fd < 0) {
            PRINT("Failed to create socket\n");
            osDelay(2000); // 2秒后重试
            continue;
        }

        // 设置服务器地址
        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(USED_TCP_SOCKET_PORT);       // 服务使用端口号
        server_addr.sin_addr.s_addr = inet_addr(CLOUD_SERVER_IP); // 服务器公网IP

        // 连接服务器
        if (lwip_connect(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            PRINT("Connection failed\n");
            lwip_close(sock_fd);
            sock_fd = -1; 
            osDelay(2000); // 2秒后重试
            continue;
        }

        PRINT("Connected to server\n");
        connect_to_server_flag = 1;

        if(connect_to_server_flag == 1)
        {
            //连接上服务器 指示灯亮起
            uapi_gpio_set_val(SERVER_CONNECT_LIGHT, GPIO_LEVEL_HIGH);
        }

        // 联网获取时间戳
        if (lwip_send(sock_fd, gettime_command, strlen(gettime_command), 0) < 0) {
            PRINT("Send failed\n");
        }
        osal_msleep(500);
        // 接收返回的时间戳 @YYYYMMDDHHMMSS
        len = lwip_recv(sock_fd, buffer, sizeof(buffer) - 1, 0);
        buffer[len] = '\0';
        PRINT("Get buffer: %s\n", buffer);
        for (i = 0; i < 150; i++)
            if (buffer[i] == '@')
                break;
        i ++;
        j = 0;
        while (i < len) {
            sys_time[j] = buffer[i];
            i++;
            j++;
        }
        PRINT("SERVER_CONNECTED,Get Time: %s\n", sys_time);
        // 向串口屏转发
        sprintf(message_to_uart, "%s%s", sys_time, envoronment);
        uapi_uart_write(UART_BUS_2, (uint8_t *)message_to_uart, strlen(message_to_uart), 50);
        memset(buffer, 0, 128);

        // 禁用小包算法
        int flag = 1;
        setsockopt(sock_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
        // 设置接收超时200ms
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 200000; 
        setsockopt(sock_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        
        // 发送和接收数据
        while (1) {
            alive_cnt ++;
            environment_cnt ++;

            // 发送数据至服务器
            // 心跳保活信息
            if (alive_cnt >= 1)
            {
                //after 1.4s
                if (lwip_send(sock_fd, message, strlen(message), 0) < 0) {
                PRINT("Send failed\n");
                break;
                }
                alive_cnt = 0;
            }
            
            // 发送环境信息
            if(environment_cnt >= 5)
            {
                if(temp != 0 && humi != 0)
                {
                    sprintf(envoronment,"T:%.2f H:%.2f",temp,humi);
                    lwip_send(sock_fd, envoronment, strlen(envoronment), 0);
                    // 将获取到的时间戳发送给串口屏
                    sprintf(message_to_uart, "%s%s", sys_time, envoronment);
                    uapi_uart_write(UART_BUS_2, (uint8_t *)message_to_uart, strlen(message_to_uart), 50);
                }
                environment_cnt = 0;
            }

            // 接收数据
            len = lwip_recv(sock_fd, buffer, sizeof(buffer) - 1, 0);
            buffer[len] = '\0';
            if(buffer[0] != 0)
                PRINT("Received: %s\n", buffer);

            // 将接收到的学习任务转发给串口屏
            if(buffer[0] == '*')
            {
                for(i = 0;i < 150;i ++)
                    task[i] = buffer[i];
                uapi_uart_write(UART_BUS_2, (uint8_t *)task, 150, 50);
            }
            memset(buffer, 0, 128);

            osDelay(200);
        }
        // 异常状态从循环中退出
        lwip_close(sock_fd);
        PRINT("Disconnected from server\n");
        connect_to_server_flag = 0;
        uapi_gpio_set_val(SERVER_CONNECT_LIGHT, GPIO_LEVEL_LOW);
        break; // 重新wifi初始化
        osDelay(2000); // 等待2秒后重连
    }
}

// wifi任务的入口 -> sta_sample_init
void wifi_entry(void)
{
    osThreadAttr_t attr;
    attr.name = "wifi_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = WIFI_TASK_STACK_SIZE;
    attr.priority = WIFI_TASK_PRIO;
    if (osThreadNew((osThreadFunc_t)sta_sample_init, NULL, &attr) == NULL) {
        PRINT("%s::Create sta_sample_task fail.\r\n", WIFI_STA_SAMPLE_LOG);
    } else
        PRINT("%s::Create sta_sample_task succ.\r\n", WIFI_STA_SAMPLE_LOG);
}

// STA模式初始化
int sta_sample_init(void *param)
{
    param = param;

    /* 注册事件回调 */
    if (wifi_register_event_cb(&wifi_event_cb) != 0) {
        PRINT("%s::wifi_event_cb register fail.\r\n", WIFI_STA_SAMPLE_LOG);
        return -1;
    }
    PRINT("%s::wifi_event_cb register succ.\r\n", WIFI_STA_SAMPLE_LOG);
    
    uapi_pin_set_mode(SERVER_CONNECT_LIGHT, HAL_PIO_FUNC_GPIO);
    uapi_gpio_set_dir(SERVER_CONNECT_LIGHT, GPIO_DIRECTION_OUTPUT);

    /* 等待wifi初始化完成 */
    while (1)
    {
        // 一直执行sta模式
        example_sta_function();
        osal_msleep(200);
    }
}