Page({
    data: {
      // 连接状态
      connectStatus: 'disconnected', // disconnected/connecting/connected
      statusText: '未连接',
      statusClass: 'status-disconnected',
      deviceOnline: false,
      
      // 服务器配置
      serverIp: '152.136.167.211', // 替换为你的阿里云ECS公网IP
      serverPort: '8080', // 替换为你的服务器端口
      socketTask: null,
    
      // 环境数据
      temperature: '——',  // 温度值
      humidity: '——',      // 湿度值
  
      // todolist
      scrollHeight: 300, // 初始滚动高度
      inputLines: [], // 存储所有输入行的数据
      inputValue: '', // 当前输入的值
      // todolist视图控制
      currentView: 'push', // push:远程推送, progress:查看进度
      // 已经完成的任务
      completedTasks: []
    },
  
    onLoad() {
      // 初始化
      this.calculateScrollHeight();
    },
  
    onUnload() {
      // 页面卸载时关闭连接
      this.disconnectDevice();
    },

    // 切换视图
    switchView(e) {
        const view = e.currentTarget.dataset.view;
        this.setData({
        currentView: view
        }, () => {
        this.calculateScrollHeight();
        });
    },
  
    // 连接/断开设备
    toggleConnect() {
      const { connectStatus ,} = this.data;
      
      if (connectStatus === 'connected') {
        this.disconnectDevice();
        return;
      }
      
      this.connectToServer();
    },
    
    // 连接到服务器
    connectToServer() {
      const { serverIp, serverPort } = this.data;
      
      this.setData({
        connectStatus: 'connecting',
        statusText: '连接中...',
        statusClass: 'status-connecting'
      });
      
      // 创建WebSocket连接
      const socketTask = wx.connectSocket({
        url: `ws://${serverIp}:${serverPort}`,
        success: () => {
          console.log('WebSocket连接创建成功');
        },
        fail: (err) => {
          console.error('WebSocket连接创建失败', err);
          this.setData({
            connectStatus: 'disconnected',
            statusText: '连接失败',
            statusClass: 'status-disconnected',
            temperature: '——',  
            humidity: '——'     
          });
          wx.showToast({
            title: '连接服务器失败',
            icon: 'none'
          });
        }
      });
      
      // 监听WebSocket打开
      socketTask.onOpen(() => {
        console.log('WebSocket连接已打开');
        this.setData({
          connectStatus: 'connected',
          statusText: '已连接',
          statusClass: 'status-connected',
          socketTask: socketTask
        });
        
        // 监听服务器消息
        socketTask.onMessage((res) => {
          console.log('收到服务器消息:', res.data);
          
          // 区分处理不同类型的数据
          if (res.data instanceof ArrayBuffer) {
            // 图像数据
            this.handleImageData(res.data);
          } else {
            // 控制命令
            this.handleServerMessage(res.data);
          }
        });
      });
      
      // 监听WebSocket错误
      socketTask.onError((err) => {
        console.error('WebSocket错误:', err);
        this.setData({
          connectStatus: 'disconnected',
          statusText: '连接错误',
          statusClass: 'status-disconnected',
          socketTask: null
        });
      });
      
      // 监听WebSocket关闭
      socketTask.onClose(() => {
        console.log('WebSocket连接已关闭');
        this.setData({
          connectStatus: 'disconnected',
          statusText: '未连接',
          statusClass: 'status-disconnected',
          socketTask: null,
          deviceOnline: false,
          temperature: '——',  
          humidity: '——'  
        });
      });
    },
    
    // 处理服务器消息
    handleServerMessage(message) {
      // 先判断是否是字符串消息（控制命令）
      if (typeof message === 'string') {
        try {
          const data = JSON.parse(message);
          
          if (data.type === 'device_status') {
            const isOnline = data.status === 'on';
            this.setData({
              deviceOnline: isOnline
            });

            if (!isOnline) {
                this.setData({
                  temperature: '——', 
                  humidity: '——'   
                });
              }
            
            wx.showToast({
              title: isOnline ? '设备已上线' : '设备未上线',
              icon: 'none'
            });
          }
          else if (data.type === 'environment') {
            if (this.data.deviceOnline) {
                this.setData({
                  temperature: data.temperature,
                  humidity: data.humidity
                });
              }
          }
          else if (data.type === 'delete' && data.task) {
            this.processTaskDeletion(data.task);
          }
        } catch (e) {
          console.error('解析服务器消息失败:', e);
        }
      } 
    },

    clearCurrentView() {
        if (this.data.currentView === 'push') {
            // 清除推送界面的所有任务
            this.setData({
                inputLines: []
            }, () => {
                wx.showToast({
                    title: '任务列表已清空',
                    icon: 'success'
                });
                this.calculateScrollHeight();
            });
        } else if (this.data.currentView === 'progress') {
            // 清除进度界面的完成记录
            this.setData({
                completedTasks: []
            }, () => {
                wx.showToast({
                    title: '完成记录已清空',
                    icon: 'success'
                });
            });
        }
    },

    // 处理任务删除指令
    processTaskDeletion(taskName) {
    // 删除远程推送页面的对应任务
    const inputLines = this.data.inputLines.filter(item => 
      item.value.trim() !== taskName
    );
    
    // 添加到已完成任务列表
    const date = new Date();
    const time = `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    const newCompletedTask = {
      task: taskName,
      time: time
    };
    
    this.setData({
      inputLines: inputLines,
      completedTasks: [newCompletedTask, ...this.data.completedTasks]
    });
    
    wx.showToast({
      title: `任务 "${taskName}" 已完成`,
      icon: 'success'
    });
    
    // 计算滚动高度
    this.calculateScrollHeight();
    },
    
    // 断开设备连接
    disconnectDevice() {
      const { socketTask } = this.data;
      if (socketTask) {
        socketTask.close({
          success: () => {
            console.log('WebSocket连接已主动关闭');
          }
        });
      }
      
      this.setData({
        connectStatus: 'disconnected',
        statusText: '未连接',
        statusClass: 'status-disconnected',
        socketTask: null,
        deviceOnline: false,
        temperature: '——', 
        humidity: '——'    
      });
    },
    
    // 发送任务列表
    sendTaskList() {
      const { socketTask, connectStatus, inputLines ,deviceOnline} = this.data;
      
      if (connectStatus !== 'connected' || !socketTask) {
        wx.showToast({
          title: '未连接到服务器',
          icon: 'none'
        });
        return;
      }

        // 检查设备是否在线
        if (!deviceOnline) {
            wx.showToast({
            title: '设备未上线，无法发送任务',
            icon: 'none'
            });
            return;
        }
      
      // 过滤空任务并提取任务内容
      const tasks = inputLines
        .filter(item => item.value.trim() !== '')
        .map(item => item.value.trim());
      
      if (tasks.length === 0) {
        wx.showToast({
          title: '没有有效的任务可发送',
          icon: 'none'
        });
        return;
      }
      
      const command = JSON.stringify({
        type: 'task_list',
        tasks: tasks
      });
      
      socketTask.send({
        data: command,
        success: () => {
          wx.showToast({
            title: '任务列表已发送',
            icon: 'success'
          });
          console.log('已发送任务列表:', tasks);
        },
        fail: (err) => {
          console.error('发送任务列表失败:', err);
          wx.showToast({
            title: '发送任务列表失败',
            icon: 'none'
          });
        }
      });
    },
  
    calculateScrollHeight() {
      const query = wx.createSelectorQuery();
      query.select('.todolist-section').boundingClientRect();
      query.select('.todolist_top').boundingClientRect();
      query.exec(res => {
        const sectionHeight = res[0].height;
        const topHeight = res[1].height;
        const padding = 20; // 上下边距
        this.setData({
          scrollHeight: sectionHeight - topHeight - padding
        });
      });
    },
  
    // 添加新行
    addNewLine() {
      this.setData({
        inputLines: [...this.data.inputLines, { value: '' }]
      }, () => {
        this.calculateScrollHeight();
      });
    },
  
    // 删除行
    removeLine(e) {
      const index = e.currentTarget.dataset.index;
      const newLines = this.data.inputLines.filter((_, i) => i !== index);
      this.setData({
        inputLines: newLines
      }, () => {
        this.calculateScrollHeight();
      });
    },
  
    // 输入处理
    onInput: function(e) {
      const index = e.currentTarget.dataset.index;
      const value = e.detail.value;
      const newLines = this.data.inputLines.map((line, i) => 
        i === index ? {...line, value} : line
      );
      this.setData({
        inputLines: newLines,
        inputValue: value
      });
    },
  
    // 添加任务
    addTask: function(e) {
      const index = e.currentTarget.dataset.index;
      const value = e.detail.value;
      if (value.trim()) {
        // 这里可以添加任务处理逻辑
        console.log('添加任务:', value);
        // 清空当前输入
        const newLines = this.data.inputLines.map((line, i) => 
          i === index ? {...line, value: ''} : line
        );
        this.setData({
          inputLines: newLines,
          inputValue: ''
        });
      }
    },
  });