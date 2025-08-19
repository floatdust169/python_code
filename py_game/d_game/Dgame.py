import pygame  
import random  
import sys  
import math
  
# 初始化Pygame  
pygame.init()  
pygame.mixer.init()
  
# 屏幕尺寸  
screen_width = 800  
screen_height = 300  
ground_height = 15
screen = pygame.display.set_mode((screen_width, screen_height))  
pygame.display.set_caption("Google Dino Game")  
icon = pygame.image.load("pic\dino\REXblue.png")  
pygame.display.set_icon(icon) 
  
# 颜色定义  
BLACK = (0, 0, 0)  
WHITE = (255, 255, 255)  
Grey = (128,128,128)
GREEN = (0, 255, 0)  
RED = (255, 0, 0)  

class GameState:  
    # 游戏状态
    PLAYING = 1  
    DEAD = 2  
    START_SCREEN = 3 

# 定义背景云
class Cloud:
    def __init__(self):
        self.image = pygame.image.load('pic/cloud.png')
        self.width, self.height = self.image.get_size()
        self.x = random.randint(0, screen_width)    
        self.y = random.randint(0, screen_height // 2)    
        self.speed = 5
    
    def update(self,speed): 
        self.speed = speed
        self.x -= self.speed
        if self.x <= -self.width:
            self.x = screen_width - self.width 

    def draw(self, screen):    
        screen.blit(self.image, (self.x, self.y))
Cloud_num = 15
cloud = [Cloud() for _ in range(Cloud_num)] 
  
# 恐龙类  
class Dino:  
    def __init__(self):  
        # 图片资源
        self.images = [pygame.image.load("pic\dino\REXblue.png"),
                       pygame.image.load("pic\dino\lREX.png"),
                       pygame.image.load("pic/dino/rREX.png"),
                       pygame.image.load("pic\dino\dREX.png"),
                       ]  
        self.image_index = 0  
        self.image = self.images[self.image_index]  
        self.mask = pygame.mask.from_surface(self.image.convert_alpha())
        # 尺寸、坐标信息
        self.rect = self.image.get_rect()  
        self.rect.x = 50  
        self.rect.y = screen_height - self.rect.height - 15
        self.init_y = screen_height - self.rect.height - 15
        # 跳跃
        self.jumping = False  
        self.jump_speed = 15
        self.gravity = 0.5  
        self.velocity = 0  
        
    def update(self,game_state):  
        # 动画  
        #帧动画
        if game_state == GameState.DEAD:
            self.image = self.images[3]  
        else:
            self.image_index = 1 + (self.image_index + 0.7) % 2  
            self.image = self.images[int(self.image_index)]  
        
        # 重力  
        if self.jumping:  
            self.velocity += self.gravity  
            self.rect.y += self.velocity  
            if self.rect.bottom >= screen_height - 10:  
                self.rect.bottom = screen_height - 10  
                self.jumping = False  
                self.velocity = 0  
        else:  
            self.rect.y = screen_height - self.rect.height - 10  
  
    def draw(self, screen):  
        screen.blit(self.image, self.rect)  
  
    def jump(self):  
        if not self.jumping:  
            self.jumping = True  
            self.velocity = -self.jump_speed  

# 障碍物类  
class Obstacle:  
    def __init__(self,game_sec):  
        self.imagelib = [pygame.image.load("pic\cactus\p1.png"),
                         pygame.image.load("pic\cactus\p2.png"),
                         pygame.image.load("pic\cactus\p3.png"),
                         pygame.image.load("pic\cactus\p4.png"),
                         pygame.image.load("pic\obird.png")]
        if game_sec < 10:
            self.image = self.imagelib[random.randint(0,3)]
            self.rect = self.image.get_rect()  
            self.rect.y = screen_height - self.rect.height - 5
        else:
            if random.randint(0,3) <= 1:
                self.image = self.imagelib[random.randint(0,3)]
            else:
                self.image = self.imagelib[4]
            self.rect = self.image.get_rect()  
            if self.image == self.imagelib[4]:
                self.rect.y = random.randint(int(screen_height / 2),screen_height - ground_height - 40)
            else:
                self.rect.y = screen_height - self.rect.height - 5
        self.mask = pygame.mask.from_surface(self.image.convert_alpha())
        # 初始化生成的障碍物在屏幕右侧刷新
        self.rect.x = screen_width  
        self.speed = 5

    def update(self,speed):  
        self.speed = speed
        self.rect.x -= self.speed 
  
    def draw(self, screen):  
        screen.blit(self.image, self.rect)  
  
    def is_off_screen(self):  
        return self.rect.right < 0 

# 游戏主循环  
def main():  
    pygame.mixer.music.load('sound/lgdxq.mp3') 
    pygame.mixer.music.set_volume(0.2)
    dino = Dino()  
    obstacles = [Obstacle(0)]                                       # 初始化障碍物  
 
    # 游戏控制
    skip_space = 0                                                  # skip first space down
    game_state = GameState.START_SCREEN  
    start_time = 0 
    clock = pygame.time.Clock() 
                                                                    # 障碍物生成计时
    Generate_Obstacle_Time_Value = random.randint(3000,5000)
    Last_Generate_Obstacle_Time = 0
    game_sec = 0                                                    # 游戏运行总时间
    global_speed = 5                                                # 游戏总速度
  
    while True:  
        for event in pygame.event.get():  
            if event.type == pygame.QUIT:  
                pygame.quit()  
                sys.exit()  
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:  
                if game_state == GameState.START_SCREEN:  
                    # 控制游戏开始
                    game_state = GameState.PLAYING  
                    start_time = pygame.time.get_ticks()
                    
                    pygame.mixer.music.play(-1)  # -1 表示循环播放    
                elif game_state == GameState.DEAD:  
                    # 游戏状态重置
                    obstacles = [Obstacle(0)]  # 重置障碍物  
                    dino.rect.y = screen_height - dino.rect.height - 5 
                    dino.jumping = False  
                    dino.velocity = 0  
                    game_state = GameState.PLAYING  
                    start_time = pygame.time.get_ticks()  

                    pygame.mixer.music.play(-1)  # -1 表示循环播放    
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_SPACE) and (skip_space != 0): 
                        dino.jump()
                    else: skip_space = 1

        # 仅在游戏进行时更新和绘制  
        if game_state == GameState.PLAYING:  
            global_speed = 5 + int(15 * (math.tanh(game_sec / 30 *0.55)))
            # 更新游戏状态  
            # 计算游戏时间（用于控制障碍物速度和动画等）  
            game_time = pygame.time.get_ticks() - start_time 
            game_sec = game_time / 1000.0

            # 恐龙主体的更新
            dino.update(game_state)                                   
            # 障碍物的更新：远离屏幕从列表中删除再追加
            if game_time - Last_Generate_Obstacle_Time >= Generate_Obstacle_Time_Value:  
                # 从屏幕最右边生成一个新的障碍物   
                new_obstacle = Obstacle(game_sec)  
                obstacles.append(new_obstacle)  
                Last_Generate_Obstacle_Time = game_time 
                # Generate_Obstacle_Time_Value = random.randint(1000,3000)
                
                Generate_Obstacle_Time_Value = random.randint(1000 - int(1000 * (math.tanh(game_sec / 30 *0.55)))
                                                              ,3000 - int(3000 * (math.tanh(game_sec / 30 *0.55))))
                                                              
            for obstacle in obstacles:                      
                obstacle.update(speed = global_speed)  
                if obstacle.is_off_screen():  
                    obstacles.remove(obstacle)  
            for i in range(Cloud_num):
                cloud[i].update(speed = global_speed)

            # 检查碰撞  
            
            for obstacle in obstacles:  
                if dino.mask.overlap(obstacle.mask,(obstacle.rect.x - dino.rect.x,obstacle.rect.y - dino.rect.y)):
                    game_state = GameState.DEAD 
                    pygame.mixer.music.stop()
                    dino.update(game_state)      
  
            # 绘制游戏  
                # 背景
            screen.fill(WHITE)  
            pygame.draw.line(screen, Grey, (0, screen_height-ground_height), (screen_width, screen_height-ground_height), 2)  
            for _ in range(200):
                x = random.randint(0, screen_width - 1)  
                y = random.randint(screen_height - ground_height,  screen_height)  
                pygame.draw.circle(screen, Grey, (x, y), 2)  # 绘制半径为2的圆点  
                # 对象
            dino.draw(screen)  
            for obstacle in obstacles:  
                obstacle.draw(screen)  
            # 显示游戏运行时间
            time_text = f"Time: {game_sec:.2f} s"
            draw_time_text = pygame.font.Font(None, 30).render(time_text, True, BLACK)  
            screen.blit(draw_time_text, (screen.get_width() - draw_time_text.get_width() - 10, 10))

            for i in range(Cloud_num):
                cloud[i].draw(screen)

            pygame.display.flip()  
            clock.tick(60)  # 控制帧率  
        else:  
            # 显示开始屏幕或游戏结束屏幕  
            # screen.fill(WHITE)                                       
            if game_state == GameState.START_SCREEN:  
                screen.fill(WHITE)
                start_text = pygame.font.Font(None, 64).render("Press any key or click to start", True, BLACK)  
                screen.blit(start_text, (screen_width // 2 - start_text.get_width() // 2, screen_height // 2 - start_text.get_height() // 2))  
            elif game_state == GameState.DEAD:  
                # Death Init：
                skip_space = 0 
                Generate_Obstacle_Time_Value = random.randint(1000,3000)
                Last_Generate_Obstacle_Time = 0                                                   
                global_speed = 5  
                if game_sec != 0:
                    score = game_sec
                game_sec = 0 

                draw_temp_text = pygame.font.Font(None, 44).render(f"Game Over! Survival time: {score:.2f} s", True, BLACK)  
                sta_text = pygame.font.Font(None, 44).render("Game Over! Survival time: ", True, BLACK)  
                screen.blit(sta_text, (screen_width // 2 - draw_temp_text.get_width() // 2 , screen_height // 2 - draw_temp_text.get_height() // 2 - 30))
                score_text = pygame.font.Font(None, 44).render(f"{score:.2f} s", True, RED)
                screen.blit(score_text, (screen_width // 2 - draw_temp_text.get_width() // 2 + sta_text.get_width(), screen_height // 2 - draw_temp_text.get_height() // 2 - 30))
                dead_text1 = pygame.font.Font(None, 44).render("Press any key or click to try again", True, BLACK)  
                screen.blit(dead_text1, (screen_width // 2 - dead_text1.get_width() // 2, screen_height // 2 - dead_text1.get_height() // 2))  
  
            pygame.display.flip()  
            clock.tick(10)  # 降低非游戏状态时的帧率  
  
if __name__ == "__main__":  
    main()