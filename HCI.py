import cv2 as cv
import mediapipe as mp 
import mediapipe.python.solutions.hands
import numpy as np
from collections import deque
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from IconAnimator import IconAnimator
from Menu import Menu
from DataProces import Data

'''
手势交互的主文件，获取关于手势操作的所有信息
'''

# 手部交互类
class HandHCI():
    def __init__(self, staticMode=False, maxHands=2, minDetectionCon=0.75, minTrackCon=0.6):
        """
        初始化手势交互类
        
        参数:
        staticMode -- 是否静态图像模式 (默认动态视频流模式)
        maxHands -- 最大检测手数量
        minDetectionCon -- 最小检测置信度
        minTrackCon -- 最小跟踪置信度
        """
        # -------------------------------关键点识别配置-------------------------------#
        self.staticMode = staticMode
        self.maxHands = maxHands
        self.minDetectionCon = minDetectionCon
        self.minTrackCon = minTrackCon
        
        # 初始化MediaPipe手势检测工具
        self.mpDraw = mp.solutions.drawing_utils
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.staticMode,
            max_num_hands=self.maxHands,
            model_complexity=1,  # 模型复杂度 (0-2)
            min_detection_confidence=self.minDetectionCon,
            min_tracking_confidence=self.minTrackCon)
        
        # 关键点和连接线的绘制样式
        self.handLmsStyle = self.mpDraw.DrawingSpec(color=(0, 0, 255), thickness=5)  # 红色关键点
        self.handConStyle = self.mpDraw.DrawingSpec(color=(0, 255, 0), thickness=10)  # 绿色连接线
        
        # -----------------------------------手部边界框----------------------------------- #
        self.Bbox = []  # 存储检测到的手部边界框 [手类型, (x_min, y_min, x_max, y_max)]
        
        # ----------------------------------音量控制初始化------------------------------------ #
        # 获取系统默认音频输出设备
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))  # 音量控制接口
        
        # 获取系统音量范围
        self.volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = self.volRange[0], self.volRange[1]  # 音量最小值和最大值
        # ------------------------------------数据处理器--------------------------------------------#
        self.data = Data()
        # -----------------------------------菜单系统状态管理--------------------------------------- #
        self.frontPinchHistory = False          # 正手捏合的历史状态 (用于状态切换检测)(也可以是长按的判定)
        self.frontPinch = False                 # 当前正手单击瞬间的状态
        self.frontRelease = False               # 正手松开瞬间的状态
        self.Front = False                      # 当前是否为正手状态
        self.MenuBall = False                   # 菜单球存在状态
        self.Menu = False                       # 菜单存在状态
        self.PinchIndex = 0                     # 单击次数计数器
        self.point_menuball = None              # 初始化菜单定位
        self.point_menu = None
        self.TowFinger_cx = None
        self.TowFinger_cy = None
        self.TowFingerLenght = 0                # 双指距离
        
        # -----------------------------------图标动画器初始化------------------------------------------- #
        # 初始化菜单图标动画器 (带放大效果)
        self.Menu_animator = IconAnimator(r'icon_images\image copy 4.png', max_scale=4, alpha=0.7, animation_duration=0.6)
        # 初始化菜单球图标动画器 (轻微放大效果)
        self.MenuBall_animator = IconAnimator(r"icon_images\image copy 3.png", max_scale=0.8, alpha=0.8, animation_duration=0.7)

        # 初始化系统菜单
        self.menu = Menu()

    # -------------------------------手部检测函数--------------------------------#
    def findRtHands(self, img, draw=True):
        """
        检测并获取图像中的右手信息
        
        参数:
        img -- 输入图像 (BGR格式)
        draw -- 是否在图像上绘制手部关键点和边界框
        
        返回:
        list -- 检测到的右手信息列表 [["Right", 关键点列表]]
        """
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB) 
        result = self.hands.process(imgRGB)  # 处理图像获取手势信息
        
        imgHeight = img.shape[0]
        imgWidth = img.shape[1]
        
        rthand = []  # 存储识别到的右手信息
        
        if result.multi_hand_landmarks:
            # 遍历检测到的每只手及其左右手信息
            for handLms, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                hand_label = handedness.classification[0].label  # "Left" 或 "Right"
                hand_score = handedness.classification[0].score  # 置信度
                
                # 计算手部边界框
                bbox = self.handBox(img, handLms.landmark)
                x_min, y_min, x_max, y_max = bbox
                self.Bbox = ["Right", bbox]  # 更新当前边界框信息
                
                # 只处理右手
                if hand_label == "Right":
                    hand_color = (0, 0, 255)  # 红色(右手)
                    
                    if draw:
                        # 绘制手部关键点和连接线
                        self.mpDraw.draw_landmarks(
                            img, handLms, self.mpHands.HAND_CONNECTIONS,
                            self.mpDraw.DrawingSpec(color=hand_color, thickness=2, circle_radius=4),
                            self.mpDraw.DrawingSpec(color=hand_color, thickness=2))
                        
                        # 绘制边界框和标签
                        cv.rectangle(img, (x_min, y_min), (x_max, y_max), hand_color, 2)
                        cv.putText(img, "Right", (x_min, y_min - 10), 
                                   cv.FONT_HERSHEY_SIMPLEX, 0.7, hand_color, 2)
                    
                    # 收集所有关键点坐标
                    allhandkps = []
                    for i, lm in enumerate(handLms.landmark):
                        xPos = int(lm.x * imgWidth)
                        yPos = int(lm.y * imgHeight)
                        allhandkps.append([i, xPos, yPos])
                    
                    rthand.append([hand_label, allhandkps])
                    
        return rthand

    def findLfHands(self, img, draw=True):
        """
        检测并获取图像中的左手信息
        
        参数:
        img -- 输入图像 (BGR格式)
        draw -- 是否在图像上绘制手部关键点和边界框
        
        返回:
        list -- 检测到的左手信息列表 [["Left", 关键点列表]]
        """
        # 实现逻辑与findRtHands类似，但处理左手
        # ... (为节约篇幅，省略重复注释)
        imgRGB = cv.cvtColor(img,cv.COLOR_BGR2RGB) 
        result =self.hands.process(imgRGB)
        # print(result.multi_hand_landmarks) #回传手部21个关键点坐标

        imgHight = img.shape[0]
        imgWidth = img.shape[1]

        # 打包左手信息
        lfhand = []

        if result.multi_hand_landmarks:
            '''
            使用 multi_handedness属性​​MediaPipe 的输出结果中包含 multi_handedness，这是包含每只手的左右信息（"Left" 或 "Right"）和置信度的列表
            '''
            for handLms , handedness in zip(result.multi_hand_landmarks, result.multi_handedness): #遍历每只手 并获取左右手信息
                
                # 获取左手信息
                hand_label = handedness.classification[0].label  # "Left" 或 "Right"
                hand_score = handedness.classification[0].score  # 置信度

                bbox = self.handBox(img,handLms.landmark)
                x_min,y_min,x_max,y_max = bbox
                self.Bbox = ["Left",bbox]

                if hand_label == "Left":
                    hand_color = (0,255,0)

                    if draw:
                        #画出所有关键点 mpHands.HAND_CONNECTIONS:将点连线，点的样式，线的样式
                        self.mpDraw.draw_landmarks(
                        img, handLms, self.mpHands.HAND_CONNECTIONS,
                        self.mpDraw.DrawingSpec(color=hand_color, thickness=2, circle_radius=4),
                        self.mpDraw.DrawingSpec(color=hand_color, thickness=2))

                        cv.rectangle(img, (x_min, y_min), (x_max, y_max), hand_color, 2)
                        # 标签
                        cv.putText(img, "Left", (x_min, y_min - 10), 
                                cv.FONT_HERSHEY_SIMPLEX, 0.7, hand_color, 2)

                    # 记录所有的关键点信息
                    allhandkps = []
                    for i, lm in enumerate(handLms.landmark):
                        xPos = int(lm.x * imgWidth)
                        yPos = int(lm.y * imgHight)
                        allhandkps.append([i, xPos, yPos])

                    lfhand.append([hand_label,allhandkps])

        return lfhand
    
    def handBox(self, img, landmark):
        """
        计算手部边界框
        
        参数:
        img -- 输入图像 (用于获取尺寸)
        landmark -- 手部关键点列表
        
        返回:
        tuple -- 边界框坐标 (x_min, y_min, x_max, y_max)
        """
        h, w, c = img.shape
        # 从关键点获取所有x和y坐标
        x_coords = [lm.x * w for lm in landmark]
        y_coords = [lm.y * h for lm in landmark]
        # 计算边界框
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        return (x_min, y_min, x_max, y_max)

    # -------------------------------手势交互函数--------------------------------#
    def controlVol(self, img, allhands, finger1=4, finger2=8, exponent=1.0, color=(2,81,255), draw=True):
        """
        通过双指距离控制系统音量
        
        参数:
        img -- 输入图像 (用于绘制)
        allhands -- 手部信息列表
        finger1 -- 第一个手指索引 (默认4: 拇指尖)
        finger2 -- 第二个手指索引 (默认8: 食指尖)
        exponent -- 指数映射参数 (非线性控制)
        color -- 显示颜色 (默认青色)
        draw -- 是否在图像上显示音量百分比
        """
        if allhands:
            # 获取双指位置 (拇指尖和食指尖)
            x1, y1 = allhands[0][1][finger1][1], allhands[0][1][finger1][2]
            x2, y2 = allhands[0][1][finger2][1], allhands[0][1][finger2][2]
            
            # 计算两点距离
            length = cv.norm((x1, y1), (x2, y2), cv.NORM_L2)
            TowFinger_cx, TowFinger_cy = (x1 + x2) // 2, (y1 + y2) // 2  # 中点坐标
            
            # 使用指数映射计算音量百分比(显示用)
            vol_percent = self.data.ExponentialMap(length, [40, 300], [0, 100], exponent)
            
            if draw:
                cv.putText(img, f"{int(vol_percent)}%", (TowFinger_cx, TowFinger_cy), 2, 1, color, 2)
            
            # 计算实际音量值并设置系统音量
            vol = self.data.ExponentialMap(length, [40, 300], [self.minVol, self.maxVol], 0.17)
            self.volume.SetMasterVolumeLevel(vol, None)
            
            # 当距离过近时改变显示颜色(绿色)
            if length <= 40:
                color = (0, 255, 0)
            else:
                color = (2, 81, 255)

    def fingersPinch(self, allhands, finger1=4, finger2=8, maxRange=0.2):
        """
        检测双指是否捏合
        
        参数:
        allhands -- 手部信息列表
        finger1 -- 第一个手指索引
        finger2 -- 第二个手指索引
        maxRange -- 捏合判定距离阈值(相对于手框宽度)
        
        返回:
        bool -- 是否检测到捏合动作
        """
        if allhands and allhands[0][0] == self.Bbox[0]:
            boxH = self.Bbox[1][3] - self.Bbox[1][1]  # 边界框宽度

            # 获取双指位置
            x1, y1 = allhands[0][1][finger1][1], allhands[0][1][finger1][2]
            x2, y2 = allhands[0][1][finger2][1], allhands[0][1][finger2][2]
            
            # 计算两点距离
            length = cv.norm((x1, y1), (x2, y2), cv.NORM_L2)
            # 中点坐标
            self.TowFinger_cx, self.TowFinger_cy = (x1 + x2) // 2, (y1 + y2) // 2  
            # 双指距离
            self.TowFingerLenght = length
            
            # 判断是否捏合 (距离小于手框宽度的16%)
            if length <= boxH * maxRange:
                return True
            else:
                return False
        else:
            return False

    def handDistance(self, img, allhands, model=0, exponent=0.17, draw=True):
        """
        估计手部与摄像头的相对距离
        
        参数:
        img -- 输入图像
        allhands -- 手部信息列表
        model -- 距离估计模式 
                 0: 基于关键点距离(默认)
                 1: 基于边界框宽度
        exponent -- 指数映射参数
        draw -- 是否在图像上显示
        
        返回:
        int -- 距离估计值 (0-100, 值越大表示距离越近)
        """
        if allhands and allhands[0][0] == self.Bbox[0]:
            boxW = self.Bbox[1][2] - self.Bbox[1][0]
            
            if model == 0:  # 基于关键点距离(拇指和小指根部)
                x1, y1 = allhands[0][1][5][1], allhands[0][1][5][2]
                x2, y2 = allhands[0][1][17][1], allhands[0][1][17][2]
                length = int(cv.norm((x1, y1), (x2, y2), cv.NORM_L2))
                # 指数映射到0-100范围
                distance = int(self.data.ExponentialMap(length, [0, int(img.shape[0])], [0, 100], exponent))
                return 100 - distance  # 取反 (距离近则数值大)
                
            elif model == 1:  # 基于边界框宽度
                distance = int(self.data.ExponentialMap(boxW, [0, int(img.shape[0])], [0, 100], exponent))
                return 100 - distance

    def isFront(self, allhands):
        """
        判断是否为正向手掌(掌心朝向摄像头)
        
        参数:
        allhands -- 手部信息列表
        
        返回:
        bool -- 是否为正向手掌
        """
        if allhands:
            # 获取关键点(拇指和小指根部)
            x1, y1 = allhands[0][1][5][1], allhands[0][1][5][2]
            x2, y2 = allhands[0][1][17][1], allhands[0][1][17][2]
            
            length = cv.norm((x1, y1), (x2, y2), cv.NORM_L2)
            boxH = self.Bbox[1][3] - self.Bbox[1][1]  # 边界框高度
            
            # 左手检测逻辑
            if (allhands[0][0] == "Left" and 
                boxH * 0.2 <= length and 
                x1 >= x2 and y2 >= y1):
                return True
            
            # 右手检测逻辑
            elif (allhands[0][0] == "Right" and 
                 boxH * 0.2 <= length and 
                 x2 >= x1 and y1 >= y2):
                return True
            else:
                return False
        return False


    
    # -------------------------------用户界面操作函数--------------------------------#
    def HandMenu(self, img, isFront, isPinch):
        """
        唤醒菜单
        
        参数:
        img -- 输入图像
        isFront -- 是否正手状态
        isPinch -- 是否捏合状态
        
        返回:
        img -- 添加菜单球后的图像
        """
        # 检查边界框有效性

        if self.Bbox:
            # 菜单球定位
            x1, y1, x2, y2 = self.Bbox[1]
            cx, cy = (x1 + x2) // 2, y1
            # 使用EMA平滑位置
            self.point_menuball = self.data.EMA((cx-15, cy-15), 0.25)

            # 菜单定位
            x3, y3, x4, y4 = self.Bbox[1]
            cx2, cy2 = (x3 + x4) // 2, y3
            # 使用更强平滑处理
            self.point_menu = self.data.EMA((cx2-35, cy2-35), 0.1)

        # 非正手状态时的重置
        if not isFront:
            self.MenuBall = False
            self.Menu = False
            self.Front = False
            self.PinchIndex = 0
            # 重置动画
            self.Menu_animator.reset_animation()
            self.MenuBall_animator.reset_animation()
            
        # 捏合状态变更检测 (用于检测捏合动作开始)
        if isPinch != self.frontPinchHistory and isPinch:
            self.frontPinch = True  # 标记当前捏合
            self.PinchIndex += 1    # 增加捏合计数

        # 松开状态变更检测 (用于检测捏合结束)
        elif isPinch != self.frontPinchHistory and not isPinch:
            self.frontRelease = True

        else:
            self.frontPinch = False
            self.frontRelease = False
        
        self.frontPinchHistory = isPinch  # 更新历史状态

        # # 更新正手状态和捏合历史状态
        # if isFront and isPinch:
        #     self.frontPinchHistory = True
        #     self.Front = True
        # else:
        #     self.frontPinchHistory = False
            
        # 菜单的判定
        if self.frontPinch and self.PinchIndex == 1 and not self.Menu and self.Bbox:
            self.MenuBall = True
            self.Menu = False
        
        elif self.frontPinch and self.PinchIndex == 2 and self.Bbox:
                self.Menu = True
                self.MenuBall = False

        if self.frontRelease:
            cv.imwrite(f"debug_png\\frontRelease{self.PinchIndex}.png",img)
                
        print(f'长按状态: {self.frontPinchHistory}')
        print(f"单击：{self.frontPinch}")
        print(f"松开：{self.frontRelease}")

        # print(f"菜单：{self.Menu}")
        # print(f"菜单球：{self.MenuBall}")
        print(f"捏合次数：{self.PinchIndex}")

        # 更新菜单系统参数
        self.menu.updata(self.frontPinchHistory,
                         self.frontPinch,
                         self.frontRelease,
                         self.Front,
                         self.MenuBall,
                         self.Menu,
                         self.PinchIndex,
                         self.point_menuball,
                         self.point_menu,
                         (self.TowFinger_cx,self.TowFinger_cy),
                         self.TowFingerLenght)
        
        # 启动菜单
        return self.menu.RunMenu(img)
