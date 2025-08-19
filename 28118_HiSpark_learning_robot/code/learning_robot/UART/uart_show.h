# ifndef _uart_show_h
# define _uart_show_h

# include "../NET/wifista.h"
#include "lwip/sockets.h"

#define     Rx_Length                  23 /* 包头 + 选则 + 20个数据 + 包尾*/

extern uint8_t  Rx_Wind_Data[Rx_Length];
extern char Rx_Wifi_User_Data[Rx_Length];
extern char Rx_Wifi_Key_Data[Rx_Length];
extern char Rx_Memory_Delete_Data[Rx_Length];

void uart_entry(void);

# endif
