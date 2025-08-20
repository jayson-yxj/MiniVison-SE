class Data():
    
    # -------------------------------数据处理工具函数--------------------------------#
    def EMA(self, point, alpha=0.2):
        """
        指数移动平均(用于位置平滑)
        
        参数:
        point -- 当前点坐标(x, y)
        alpha -- 平滑系数(0-1, 值越小越平滑)
        
        返回:
        tuple -- 平滑后的坐标
        """
        cx, cy = point
        
        # 初始化历史点
        if not hasattr(self, 'smooth_cx'):
            self.smooth_cx = cx
            self.smooth_cy = cy
        
        # EMA平滑处理
        self.smooth_cx = self.smooth_cx * (1 - alpha) + cx * alpha
        self.smooth_cy = self.smooth_cy * (1 - alpha) + cy * alpha
        
        return (int(self.smooth_cx), int(self.smooth_cy))

    def ExponentialMap(self, length, input_range, output_range, exponent=1.0):
        """
        指数范围映射(用于非线性控制)
        
        参数:
        length -- 输入值
        input_range -- 输入范围[min, max]
        output_range -- 输出范围[min, max]
        exponent -- 指数参数(>1: 输出对输入变化敏感, <1: 输出对输入变化不敏感)
        
        返回:
        float -- 映射后的值
        """
        # 确保输入在范围内
        length = max(input_range[0], min(length, input_range[1]))
        # 归一化
        normalized = (length - input_range[0]) / (input_range[1] - input_range[0])
        # 应用指数
        exp_normalized = normalized ** exponent
        # 映射到输出范围
        return output_range[0] + exp_normalized * (output_range[1] - output_range[0])
    
    # 计算模长
    def norm(self,point1,point2):
        return int(((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5)