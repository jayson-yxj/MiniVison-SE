import cv2
import numpy as np
import time

'''
返回的是有了图标的原图像
'''

class DynamicIconOverlay:
    def __init__(self, icon_path, initial_size=None, alpha=1):

        # 加载原始图标并保留透明度
        self.original_icon = cv2.imread(icon_path, cv2.IMREAD_UNCHANGED)
        if self.original_icon is None:
            raise ValueError(f"无法加载图标: {icon_path}")
        
        # 原始尺寸
        self.original_height, self.original_width = self.original_icon.shape[:2]
        
        # 初始化大小
        if initial_size is None:
            # 默认使用原始大小
            self.icon = self.original_icon.copy()
            self.width = self.original_width
            self.height = self.original_height
        elif isinstance(initial_size, (int, float)):
            # 缩放因子
            self.set_scale(initial_size)
        elif isinstance(initial_size, tuple) and len(initial_size) == 2:
            # 指定宽度和高度
            self.set_size(initial_size[0], initial_size[1])
        else:
            raise ValueError("initial_size 必须是缩放因子或(width, height)元组")
        
        # 默认初始位置（居中）
        self.x = 0
        self.y = 0
        self.icon_visible = True
        self.last_update_time = time.time()
        
        # 透明度控制 (0.0 = 完全透明, 1.0 = 完全不透明)
        self.alpha = alpha
    
    # 设置缩放尺寸
    def set_size(self, width, height):
        # 限制最大尺寸
        max_size = 1024  # 最大尺寸限制
        width = min(max(10, width), max_size)
        height = min(max(10, height), max_size)
        
        # 调整图标大小
        self.icon = cv2.resize(self.original_icon, (int(width), int(height)))
        self.width = self.icon.shape[1]
        self.height = self.icon.shape[0]
    
    # 设置缩放系数
    def set_scale(self, scale_factor):
        # 限制缩放范围
        scale_factor = max(0.1, min(scale_factor, 10.0))
        
        # 计算新尺寸
        new_width = int(self.original_width * scale_factor)
        new_height = int(self.original_height * scale_factor)
        
        # 设置新尺寸
        self.set_size(new_width, new_height)
    
    # 设置透明度
    def set_alpha(self, alpha):
        # 确保透明度合法
        self.alpha = max(0.0, min(1.0, alpha))
    
    # 淡入动画
    def fade_in(self, duration=1.0):
        self.set_alpha(0.0)
        self.target_alpha = 1.0
        self.fade_duration = duration
        self.fade_start_time = time.time()
        self.is_fading = True
    
    # 淡出动画
    def fade_out(self, duration=1.0):
        self.set_alpha(1.0)
        self.target_alpha = 0.0
        self.fade_duration = duration
        self.fade_start_time = time.time()
        self.is_fading = True

    # 更新淡入淡出动画
    def update_fade(self):
        if not hasattr(self, 'is_fading') or not self.is_fading:
            return
        
        # 计算动画进度
        elapsed = time.time() - self.fade_start_time
        progress = min(elapsed / self.fade_duration, 1.0)
        
        # 计算当前透明度
        current_alpha = self.alpha + (self.target_alpha - self.alpha) * progress
        self.set_alpha(current_alpha)
        
        # 检查动画是否完成
        if progress >= 1.0:
            self.is_fading = False

    # 更新图标坐标
    def update_position(self, x, y):
    
        self.x = x
        self.y = y
        self.last_update_time = time.time()
    
    # 显示图标
    def show_icon(self):
        self.icon_visible = True
    
    # 隐藏图标
    def hide_icon(self):
        self.icon_visible = False
    
    def overlay(self, background):
        self.update_fade()
        
        # 如果图标不可见或完全透明，直接返回背景
        if not self.icon_visible or self.alpha <= 0.0:
            return background
        
        # 获取图标尺寸
        h, w = self.icon.shape[:2]
        
        # 获取背景尺寸
        bg_height, bg_width = background.shape[:2]
        
        # 计算可见区域
        # 图标在背景中的起始位置
        start_x = max(0, self.x)
        start_y = max(0, self.y)
        
        # 图标在背景中的结束位置
        end_x = min(self.x + w, bg_width)
        end_y = min(self.y + h, bg_height)
        
        # 计算可见区域的尺寸
        visible_width = end_x - start_x
        visible_height = end_y - start_y
        
        # 如果没有可见区域，直接返回背景
        if visible_width <= 0 or visible_height <= 0:
            return background
        
        # 计算图标中可见的部分
        # 图标中的起始偏移（如果部分在边界外）
        icon_offset_x = max(0, -self.x)
        icon_offset_y = max(0, -self.y)
        
        # 图标中的结束位置
        icon_end_x = min(w, bg_width - self.x)
        icon_end_y = min(h, bg_height - self.y)
        
        # 提取图标可见部分
        visible_icon = self.icon[
            icon_offset_y:icon_end_y,
            icon_offset_x:icon_end_x
        ]
        
        # 提取背景的ROI区域
        roi = background[start_y:end_y, start_x:end_x]
        
        # 确保ROI与图标可见部分尺寸匹配
        if roi.shape[0] != visible_height or roi.shape[1] != visible_width:
            # 调整ROI大小以匹配图标可见部分
            roi = cv2.resize(roi, (visible_width, visible_height))
        
        # 分离alpha通道
        if visible_icon.shape[2] == 4:
            b, g, r, a = cv2.split(visible_icon)
            # 应用整体透明度
            alpha = a.astype(float) / 255.0 * self.alpha
            alpha_inv = 1.0 - alpha
        else:
            b, g, r = cv2.split(visible_icon)
            # 创建透明度通道
            alpha = np.ones_like(b, float) * self.alpha
            alpha_inv = 1.0 - alpha
        
        roi = roi.astype(float)
        
        # 为每个通道进行混合
        blended_b = roi[:, :, 0] * alpha_inv + b * alpha
        blended_g = roi[:, :, 1] * alpha_inv + g * alpha
        blended_r = roi[:, :, 2] * alpha_inv + r * alpha
        
        # 合并通道
        blended = cv2.merge([blended_b, blended_g, blended_r])
        
        # 将混合后的ROI放回原图
        result = background.copy()
        result[start_y:end_y, start_x:end_x] = blended.astype(np.uint8)
        
        return result
    
        # 获取当前图标尺寸
    def get_current_size(self):
        return self.width, self.height

        # 获取原始图标尺寸
    def get_original_size(self):
        return self.original_width, self.original_height