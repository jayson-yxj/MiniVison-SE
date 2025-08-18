import cv2 as cv
import mediapipe as mp 
import mediapipe.python.solutions.hands
import numpy as np
from collections import deque
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from IconAnimator import IconAnimator

'''
手势交互的主文件，获取关于手势操作的所有信息
'''

# 手类
class HandHCI():
    def __init__(self,staticMode=False,maxHands=2,minDetectionCon=0.75,minTrackCon=0.6):
        #-------------------------------关键点识别--------------------------------#
        self.staticMode= staticMode
        self.maxHands= maxHands
        self.minDetectionCon= minDetectionCon
        self.minTrackCon= minTrackCon
        self.mpDraw = mp.solutions.drawing_utils
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.staticMode,
            max_num_hands=self.maxHands,
            model_complexity=1,
            min_detection_confidence=self.minDetectionCon,
            min_tracking_confidence=self.minTrackCon)
        
        self.mpDraw = mp.solutions.drawing_utils 
        self.handLmsStyle = self.mpDraw.DrawingSpec(color=(0,0,255), thickness=5)
        self.handConStyle = self.mpDraw.DrawingSpec(color=(0,255,0), thickness=10)
        # -----------------------------------手框----------------------------------- #
        self.Bbox=[]
        # ----------------------------------音量控制------------------------------------ #
        # 获取默认音频设备
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
        self.volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = self.volRange[0], self.volRange[1] # 本机音量的范围
        # -----------------------------------菜单UI--------------------------------------- #
        self.frontPinchHistory = False          # 正手捏合的历史状态
        self.frontPinch = False                 # 正手捏合的状态
        self.frontRelease = False               # 正手松开的状态
        self.Front = False                      # 正手的状态
        self.MenuBall = False                   # 菜单球存在状态
        self.Menu = False                       # 菜单存在状态
        self.PinchTime = deque([0], maxlen=2)   # 上一次成功捏合时间
        self.RightPinchTime = 1.0               # 合理捏合间隔时间
        self.PinchIndex = 0                     # 捏合计数器
        # -----------------------------------图标动画------------------------------------------- #
        # 初始化动画器
        self.animator = IconAnimator(r'icon_images\image copy 4.png',max_scale=4,alpha=0.7,animation_duration=0.6)
        self.MenuBall_animator = IconAnimator(r"icon_images\image copy 3.png",max_scale=0.8,alpha=0.8,animation_duration=0.7)


    # 获取右手信息列表
    def findRtHands(self,img,draw=True):
        imgRGB = cv.cvtColor(img,cv.COLOR_BGR2RGB) 
        result =self.hands.process(imgRGB)
        # print(result.multi_hand_landmarks) #回传手部21个关键点坐标

        imgHight = img.shape[0]
        imgWidth = img.shape[1]

        # 打包右手信息
        rthand = []

        if result.multi_hand_landmarks:
            '''
            使用 multi_handedness属性​​MediaPipe 的输出结果中包含 multi_handedness，这是包含每只手的左右信息（"Left" 或 "Right"）和置信度的列表
            '''
            for handLms , handedness in zip(result.multi_hand_landmarks, result.multi_handedness): #遍历每只手 并获取左右手信息
                
                # 获取右手信息
                hand_label = handedness.classification[0].label  # "Left" 或 "Right"
                hand_score = handedness.classification[0].score  # 置信度

                bbox = self.handBox(img,handLms.landmark)
                x_min,y_min,x_max,y_max = bbox
                self.Bbox = ["Right",bbox]

                if hand_label == "Right":
                    hand_color = (0,0,255)

                    if draw:
                        #画出所有关键点 mpHands.HAND_CONNECTIONS:将点连线，点的样式，线的样式
                        self.mpDraw.draw_landmarks(
                        img, handLms, self.mpHands.HAND_CONNECTIONS,
                        self.mpDraw.DrawingSpec(color=hand_color, thickness=2, circle_radius=4),
                        self.mpDraw.DrawingSpec(color=hand_color, thickness=2))

                        cv.rectangle(img, (x_min, y_min), (x_max, y_max), hand_color, 2)
                        # 标签
                        cv.putText(img, "Right", (x_min, y_min - 10), 
                                cv.FONT_HERSHEY_SIMPLEX, 0.7, hand_color, 2)

                    # 记录所有的关键点信息
                    allhandkps = []
                    for i, lm in enumerate(handLms.landmark):
                        xPos = int(lm.x * imgWidth)
                        yPos = int(lm.y * imgHight)
                        allhandkps.append([i, xPos, yPos])

                    rthand.append([hand_label,allhandkps])

        return rthand
        

    # 获取左手信息列表
    def findLfHands(self,img,draw=True):
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


    def handBox(self,img,landmark):
        h, w, c = img.shape
        x_coords = [lm.x * w for lm in landmark]
        y_coords = [lm.y * h for lm in landmark]
        # 边界框
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        bbox = (x_min, y_min, x_max, y_max)

        return bbox
    

    # 双指控制音量
    def controlVol(self,img,allhands,finger1=4,finger2=8,exponent=1.0,color=(2,81,255),draw=True):
        if allhands:
            # 获取双指的位置
            x1, y1 = allhands[0][1][finger1][1], allhands[0][1][finger1][2]
            x2, y2 = allhands[0][1][finger2][1], allhands[0][1][finger2][2]
            
            # 计算距离
            lenght = cv.norm((x1, y1), (x2, y2), cv.NORM_L2)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            # 使用指数映射计算音量百分比（用于显示）
            vol_percent = self.ExponentialMap(lenght, [40, 300], [0, 100],exponent)

            if draw:
                cv.putText(img, f"{int(vol_percent)}%", (cx, cy), 2, 1, color, 2)
            
            # 使用指数映射设置实际音量
            vol = self.ExponentialMap(lenght, [40, 300], [self.minVol, self.maxVol],0.17)
            self.volume.SetMasterVolumeLevel(vol, None)
            
            # 当距离小于40时改变颜色
            if lenght <= 40:
                color = (0, 255, 0)
            else:
                color = (2, 81, 255)


    # 双指捏合判定
    def fingersPinch(self,allhands,finger1=4,finger2=8,maxRange=0.16):
        if allhands and allhands[0][0] == self.Bbox[0]:

            boxW = self.Bbox[1][2]-self.Bbox[1][0]
            # print(boxH)

            # 获取双指的位置
            x1, y1 = allhands[0][1][finger1][1], allhands[0][1][finger1][2]
            x2, y2 = allhands[0][1][finger2][1], allhands[0][1][finger2][2]
            
            # 计算距离
            lenght = cv.norm((x1, y1), (x2, y2), cv.NORM_L2)
            
            # 当距离小于范围
            if lenght <= boxW*maxRange:
                return True
            else:
                return False
            
        else:
            return False
        
    
    # 手掌距离
    def handDistance(self,img,allhands,model=0,exponent=0.17,draw=True):
        if allhands and allhands[0][0] == self.Bbox[0]:
            boxW = self.Bbox[1][2]-self.Bbox[1][0]
            # 关节定位深度
            if model==0:
                x1, y1 = allhands[0][1][5][1], allhands[0][1][5][2]
                x2, y2 = allhands[0][1][17][1], allhands[0][1][17][2]
                # print(x1,y1)
                # print(x2,y2)
                lenght = int(cv.norm((x1,y1),(x2,y2),cv.NORM_L2))
                # print(lenght)

                distance = int(self.ExponentialMap(lenght,[0,int(img.shape[0])],[0,100],exponent))
                # print(100-distance)
            
            # 框宽定位深度
            elif model==1:
                distance = int(self.ExponentialMap(boxW,[0,int(img.shape[0])],[0,100],exponent))

            return 100-distance
        
    
    # 判断正反手
    def isFront(self,allhands):
        if allhands:
        # 获取关节5和17信息
            x1, y1 = allhands[0][1][5][1], allhands[0][1][5][2]
            x2, y2 = allhands[0][1][17][1], allhands[0][1][17][2]

            lenght = cv.norm((x1,y1),(x2,y2),cv.NORM_L2)
            boxH = self.Bbox[1][3]-self.Bbox[1][1]
            
            if allhands[0][0] == "Left" and boxH*0.2<=lenght and x1>=x2 and y2>=y1:
                return True

            elif allhands[0][0] == "Right" and boxH*0.2<=lenght and x2>=x1 and y1>=y2:
                return True
            
            else:
                return False
            
# ------------------------------------------------------------数据处理方法-----------------------------------------------------------#
    # 运动平滑处理
    def EMA(self,point,alpha=0.2):
        cx,cy = point

        # 如果之前没有存储平滑坐标，则初始化
        '''
        ​​hasattr(object, 'attribute_name')​​
        检查 object是否有一个名为 'attribute_name'的属性，
        返回 True或 False'''

        # 历史点
        if not hasattr(self, 'smooth_cx'):
            self.smooth_cx = cx
            self.smooth_cy = cy

        # 当前点
        target_x = cx
        target_y = cy

        # 指数移动平均（EMA）平滑处理
        # alpha = 0.2  # 平滑系数（0.1~0.3 之间，越小越平滑）
        self.smooth_cx = self.smooth_cx * (1 - alpha) + target_x * alpha # 这就是一个权重计算
        self.smooth_cy = self.smooth_cy * (1 - alpha) + target_y * alpha
        point = (int(self.smooth_cx),int(self.smooth_cy))

        return point


    # 指数范围映射
    def ExponentialMap(self,length, input_range, output_range,exponent=1.0):
        length = max(input_range[0], min(length, input_range[1]))
        normalized = (length - input_range[0]) / (input_range[1] - input_range[0])
        exp_normalized = normalized ** exponent
        return output_range[0] + exp_normalized * (output_range[1] - output_range[0])
    
# --------------------------------------------------------------UI操作------------------------------------------------------------- #

    # 唤醒菜单球
    def AwakenMenuBall(self,img,isFront,isPinch, color=(255, 255, 0)):
        if self.Bbox:
            # 保险：防止误触
            boxW = self.Bbox[1][2]-self.Bbox[1][0]
            # print(f'boxW: {boxW}')
# -------------------------------------单次捏合判定----------------------------------------- #

        # 判断捏合是否突变，突变就为true (判断按下就and isPinch 松开就and not isPinch)
        if isPinch != self.frontPinchHistory and  isPinch:
            self.frontPinch = True
            # 正确捏合计数器++
            self.PinchIndex += 1
            # 记录历史点
            self.frontPinchHistory = isPinch

            # print(f"ispinch: {isPinch}")
            # print(f"self.frontPinchHistory: {self.frontPinchHistory}")
            # print(f"self.frontPinch: {self.frontPinch}")
        
        # 判断松开
        elif isPinch != self.frontPinchHistory and not isPinch:
            self.frontRelease = True

        else:
            self.frontPinch = False
            self.frontRelease = False

# ------------------------------------------------------------------------------ #
        if isFront and isPinch:
            # 更新正手捏合的状态
            self.frontPinchHistory = True
            # 更新正手的状态
            self.Front = True
        else:
            # 更新正手捏合的状态
            self.frontPinchHistory = False
# ------------------------------------------------------------------------------ #

        if self.frontPinch and self.PinchIndex == 1:
            # 更新菜单球的状态
            self.MenuBall = True
# ------------------------------------------------------------------------------ #

        if not isFront:
            # 更新菜单球的状态
            self.MenuBall = False
            # 更新菜单的状态
            self.Menu = False
            # 更新正手的状态
            self.Front = False
            # 计数器归零
            self.PinchIndex = 0

            # 动画状态重置
            self.animator.reset_animation()
            self.MenuBall_animator.reset_animation()
        

        print(f"捏合: {self.frontPinch}")
        print(f"正手: {isFront}")
        print(f'捏合计数器: {self.PinchIndex}')
# ------------------------------------------------------------------------------------ #

        if self.Bbox:
        # Bbox 中点坐标
            x1, y1, x2, y2 = self.Bbox[1]
            cx, cy = (x1 + x2) // 2, y1

            # EMA平滑处理
            point = self.EMA((cx-15,cy-15),0.25)

            if self.MenuBall and not self.Menu:
                # cv.circle(img, point, 20, color, 2)
                # self.IconMenuBall.update_position(point[0]-15,point[1]-15)
                # return self.IconMenuBall.overlay(img)
                return self.MenuBall_animator.draw_growing_matrix2(img,(point[0]-15,point[1]-15))


    # 唤醒菜单
    def AwakenMenu(self,img):
        if self.Bbox:
            # Bbox 中点坐标
            x1, y1, x2, y2 = self.Bbox[1]
            cx, cy = (x1 + x2) // 2, y1
            point = self.EMA((cx-35,cy-35),0.1)

        # 菜单显示的判定
        if self.MenuBall and self.frontPinch and self.PinchIndex == 2:
            self.Menu = True
        
        # 反手就退出
        if not self.Front:
            self.Menu = False
            self.MenuBall = False

        print(f'系统内记录的正手: {self.Front}')
        print(f'菜单球: {self.MenuBall}')
        print(f'菜单: {self.Menu}')

        # 菜单动画
        if self.Menu:
            print(f'返回图像：{self.animator.draw_growing_matrix2(img,(point[0]-15,point[1]-15))}')
            return self.animator.draw_growing_matrix2(img,(point[0]-15,point[1]-15))

        
            