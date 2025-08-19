# include "app_init.h"
# include "NET/wifista.h"
# include "UART/uart_show.h"
# include "PWM/wind.h"
# include "AHT20/aht20_task.h"

// wifi信号灯GPIO03
app_run(AHT20TASK_entry);
app_run(wifi_entry);
app_run(uart_entry);
app_run(pwm_entry);