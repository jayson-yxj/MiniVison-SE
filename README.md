
# MiniVison-SE

基于计算机视觉的手势交互系统，利用MediaPipe实时检测手部关键点，实现手势控制计算机音量和菜单交互功能（demo）（更多功能正在开发中!!!）


## 功能特性

-   🖐 实时手部检测与关键点识别
    
-   🔊 手势音量控制（双指捏合滑动调节系统音量）
-   📱 代替电脑的鼠标（正在开发）
-   🖐 功能窗口的手势拖拽（正在开发）
    
-   📱 非接触式菜单唤醒与控制
    
-   🔍 智能手势识别（捏合检测、正反手判断）
    
-   ✨ 动态UI元素（菜单球与主菜单动画效果）
    
-   🚫 防误触设计（非正手状态自动重置）
    

## 系统依赖

### 必需库

```
pip install opencv-python mediapipe pycaw comtypes numpy
```

### 可选依赖（用于高级动画效果）

```
pip install pyglet
```

## 快速开始

1.  克隆仓库
    

```
git clone https://github.com/jayson-yxj/MiniVison-SE.git
cd MiniVison-SE
```

1.  运行主程序
    

```
python main.py
```

## 基本使用

```
import numpy as np
import cv2 as cv
from  HCI  import  HandHCI

def  main():
	AllTestPath = r'video\AllTest.mp4'
	cap = cv.VideoCapture(AllTestPath)
	hand = HandHCI()

		while 1:
		succes,img = cap.read()
		if succes :

		# 获取左手的信息
		lfhand = hand.findLfHands(img)
		# 获取右手的信息
		rthand = hand.findRtHands(img)

		# 右手控制音量
		hand.controlVol(img,rthand)

		# 获取捏合信息
		isFront = hand.isFront(lfhand,False)
		# 获取手的正反
		isPinch = hand.fingersPinch(lfhand,False)

		# 菜单球跳出
		img2 = hand.AwakenMenuBall(img,isFront,isPinch)

		# 菜单跳出
		img3 = hand.AwakenMenu(img)

		if img2 is not None and img2.size >  0:
			img = img2

		elif img3 is not None and img3.size >  0:
			img = img3
		cv.imshow("img",img)

		if cv.waitKey(1) == 27:
		break

if __name__ == '__main__':
	main()
```

## 系统交互说明

### 基本手势

```
✌️ 反手拇指+食指捏合

 1. 确认

🤚 掌心朝向摄像头并捏合一次

 1. 激活菜单球

🤚 掌心朝向摄像头并捏合两次

1. 激活菜单

🤚 掌心背向摄像头
 1. 退出菜单
```
### 菜单操作


1.  ​**​唤醒菜单球​**​：
    
    -   掌心朝摄像头保持1秒
        
    -   执行一次捏合动作
        
    -   ✅ 绿色菜单球出现
        
2.  ​**​唤醒主菜单​**​：
    
    -   菜单球显示状态下
        
    -   执行第二次捏合动作
        
    -   ✅ 菜单展开动画
        

## 项目结构

```
gesture-interaction-system/
├── HandHCI.py             # 主控模块
├── IconAnimator.py        # 动画效果模块
├── UIIcon.py			   # UI图标显示模块
├── main.py                # 示例主程序
├── icon_images/           # 菜单图标资源
│   ├── image copy 3.png   # 菜单球图标
│   └── image copy 4.png   # 主菜单图标
└── README.md
```

## 高级定制

### 调节参数

```
# 初始化时可调节参数
hand_system = HandHCI(
    staticMode=False,         # 静态图像模式(False为视频流模式)
    maxHands=2,              # 最大检测手数
    minDetectionCon=0.75,     # 检测置信度阈值
    minTrackCon=0.6,          # 追踪置信度阈值
    exponent=0.17             # 音量非线性映射指数
)
```

### 自定义交互

```
# 添加新手势检测
def customGesture(self, hand_points):
    thumb_tip = hand_points[4]  # 拇指尖
    index_tip = hand_points[8]  # 食指尖
    
    # 实现自定义手势逻辑
    ...
    return gesture_detected
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1.  Fork 本项目
    
2.  创建您的功能分支 (`git checkout -b feature/new-feature`)
    
3.  提交更改 (`git commit -am 'Add new feature'`)
    
4.  推送分支 (`git push origin feature/new-feature`)
    
5.  创建Pull Request
    

## 许可协议

本项目基于 [MIT License](https://yuanbao.tencent.com/chat/naQivTmsDa/LICENSE)开源。

## 致谢

-   MediaPipe团队提供的优秀手部追踪方案
    
-   Pycaw开发者提供的Windows音频控制接口
    
-   Google Research的开源计算机视觉研究
