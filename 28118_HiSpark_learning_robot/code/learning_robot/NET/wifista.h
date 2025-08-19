#ifndef __wifista_H
#define __wifista_H

#include "pinctrl.h"
#include "gpio.h"
#include "../AHT20/aht20_task.h"
#include "../UART/uart_show.h"

# define SERVER_CONNECT_LIGHT GPIO_03

extern char sys_time[15]; // 时间格式 YYYYMMDDHHMMSS
extern char task[150];
extern int sock_fd;

void wifi_entry(void);

#endif