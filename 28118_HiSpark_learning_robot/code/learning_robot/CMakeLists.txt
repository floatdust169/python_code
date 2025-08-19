include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_subdirectory_if_exist(NET)
add_subdirectory_if_exist(AHT20)
add_subdirectory_if_exist(UART)
add_subdirectory_if_exist(PWM)

set(SOURCES_LIST
    ${CMAKE_CURRENT_SOURCE_DIR}/main_app.c

    ${CMAKE_CURRENT_SOURCE_DIR}/NET/wifista.c

    ${CMAKE_CURRENT_SOURCE_DIR}/AHT20/aht20.c  
    ${CMAKE_CURRENT_SOURCE_DIR}/AHT20/aht20_task.c  

    ${CMAKE_CURRENT_SOURCE_DIR}/UART/uart_show.c  
    ${CMAKE_CURRENT_SOURCE_DIR}/PWM/wind.c
)

set(PUBLIC_HEADER_LIST
    ${CMAKE_CURRENT_SOURCE_DIR}/NET/wifista.h

    ${CMAKE_CURRENT_SOURCE_DIR}/AHT20/aht20.h
    ${CMAKE_CURRENT_SOURCE_DIR}/AHT20/aht20_task.h  

    ${CMAKE_CURRENT_SOURCE_DIR}/UART/uart_show.h
    ${CMAKE_CURRENT_SOURCE_DIR}/PWM/wind.h
)

set(SOURCES "${SOURCES_LIST}" PARENT_SCOPE)
set(PUBLIC_HEADER "${PUBLIC_HEADER_LIST}" PARENT_SCOPE)
