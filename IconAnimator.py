import cv2 as cv
import numpy as np
from UIIcon import DynamicIconOverlay
import time

'''
返回的是图标动画的逐帧图像
'''

class IconAnimator:
    def __init__(self, icon_path,max_scale=2,alpha=1,animation_duration=1.0):
        # 创建图标叠加器
        self.Icon = DynamicIconOverlay(icon_path, initial_size=0.1,alpha=alpha)
        
        # 动画参数
        self.min_scale = 0.1  # 最小缩放比例
        self.max_scale = max_scale  # 最大缩放比例
        self.animation_duration = animation_duration  # 动画持续时间（秒）
        
        # 初始化动画状态
        self.animation_start_time = None
        self.current_scale = self.min_scale
        self.animation_complete = False  # 动画是否完成
    
    def draw_growing_matrix2(self, img, center):
        # 如果动画已经完成（达到最大尺寸），直接绘制最大尺寸图标
        if self.animation_complete:
            width, height = self.Icon.get_current_size()
            half_width = width // 2
            half_height = height // 2
            self.Icon.update_position(center[0] - half_width, center[1] - half_height)

            # cv.imshow('动画达到最大尺寸',self.Icon.overlay(img))
            return self.Icon.overlay(img)
        
        # 初始化动画开始时间
        if self.animation_start_time is None:
            self.animation_start_time = time.time()
        
        # 计算动画进度 (0.0 - 1.0)
        elapsed = time.time() - self.animation_start_time
        progress = min(elapsed / self.animation_duration, 1.0)
        
        # 计算当前缩放比例（使用缓动函数）
        ease_progress = self.ease_in_out(progress)
        self.current_scale = self.min_scale + (self.max_scale - self.min_scale) * ease_progress
        
        # 设置图标缩放
        self.Icon.set_scale(self.current_scale)
        
        # 获取当前图标尺寸
        width, height = self.Icon.get_current_size()
        half_width = width // 2
        half_height = height // 2
        
        # 更新图标位置（居中显示）
        self.Icon.update_position(center[0] - half_width, center[1] - half_height)
        
        # 叠加图标到图像
        result_img = self.Icon.overlay(img)
        
        # 检查动画是否完成
        if progress >= 1.0:
            self.animation_complete = True

        # cv.imshow("result2",result_img)
        # print(f'图标动画返回的图像：{result_img}')
        
        return result_img
    
    def ease_in_out(self, t):
        """缓入缓出函数"""
        if t < 0.5:
            return 2 * t * t
        else:
            return -1 + (4 - 2 * t) * t
    
    def reset_animation(self):
        """重置动画状态"""
        self.animation_start_time = None
        self.current_scale = self.min_scale
        self.animation_complete = False  # 动画是否完成
    
    def set_animation_speed(self, duration):
        """设置动画速度（持续时间）"""
        self.animation_duration = max(0.1, duration)
    
    def set_scale_range(self, min_scale, max_scale):
        """设置缩放范围"""
        self.min_scale = max(0.01, min_scale)
        self.max_scale = min(10.0, max_scale)
        self.animation_complete = False
    
    def is_animation_complete(self):
        """检查动画是否完成"""
        return self.animation_complete

 