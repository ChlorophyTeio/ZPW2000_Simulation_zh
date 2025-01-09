import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMessageBox
)

from QtGui.simulationUi import Ui_mainForm


class CustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_color = None  # 默认为 None，使用系统默认前景色
        self.line_thickness = 4  # 默认线条粗细
        self.draw_left_slash = True  # 默认绘制左倾斜线
        self.draw_right_slash = True  # 默认绘制右倾斜线

    def set_custom_color(self, color: QColor):
        """设置自定义颜色"""
        self.custom_color = color
        self.update()  # 触发重绘

    def set_line_thickness(self, thickness: int):
        """设置线条粗细"""
        self.line_thickness = thickness
        self.update()

    def set_slash_direction(self, left_slash: bool, right_slash: bool):
        """
        设置斜线方向
        :param left_slash: 是否绘制左倾斜线（左上到右下）
        :param right_slash: 是否绘制右倾斜线（左下到右上）
        """
        self.draw_left_slash = left_slash
        self.draw_right_slash = right_slash
        self.update()

    def paintEvent(self, event):
        # 创建 QPainter 对象
        painter = QPainter(self)

        # 获取窗口大小
        width = self.width()
        height = self.height()

        # 获取普通画笔颜色（优先使用自定义颜色，否则使用系统前景色）
        color = self.custom_color or self.palette().color(self.foregroundRole())
        pen = QPen(color)
        pen.setWidth(self.line_thickness)  # 设置线条粗细
        painter.setPen(pen)

        # 根据用户设置的方向绘制普通斜线
        if self.draw_left_slash:  # 绘制左倾斜线
            painter.drawLine(0, 0, width, height)
        if self.draw_right_slash:  # 绘制右倾斜线
            painter.drawLine(0, height, width, 0)

        painter.end()


class mainUi(QWidget, Ui_mainForm):
    def __init__(self):
        super(mainUi, self).__init__()
        self.main_ui = Ui_mainForm()
        self.main_ui.setupUi(self)
        self.setupUi(self)

        self.first_flag = False

        # 初始化倍速属性
        self.simulation_speed = 1.0
        self.is_paused = False

        # 绑定滑块的值变化信号到槽函数
        self.accelerateSlider.setMinimum(-10)
        self.accelerateSlider.setMaximum(10)
        self.accelerateSlider.setValue(0)  # 设置默认值为 0
        self.accelerateSlider.valueChanged.connect(self.update_simulation_speed)

        # 初始化轨道长度
        self.track_length = 1500  # 每段轨道长度，单位为 m

        # 列车长度属性
        self.train0_length = 209  # 默认8编组长度，单位为 m
        self.train1_length = 209  # 默认8编组长度，单位为 m

        self.train0_nounBox.currentIndexChanged.connect(self.update_train_length)

        # 设置列车初始轨道
        self.train0_current_track = self.train0_trackBox.value()  # 列车 0 初始区段
        self.train1_current_track = self.train1_trackBox.value()  # 列车 1 初始区段

        # 设置列车在轨道上的初始位置（距离下一个区段的位置）
        self.train0_position_in_track = float(self.train0_positionEdit.text())  # 获取初始位置
        self.train1_position_in_track = float(self.train1_positionEdit.text())  # 获取初始位置

        # 根据初始位置计算剩余距离
        self.train0_remaining_distance = self.track_length - self.train0_position_in_track
        self.train1_remaining_distance = self.track_length - self.train1_position_in_track

        # 初始化速度
        self.train0_speed = float(self.train0_speedEdit.text()) / 3.6  # 转换为 m/s
        self.train1_speed = float(self.train1_speedEdit.text()) / 3.6  # 转换为 m/s

        # 初始化剩余时间
        self.train0_remaining_time = self.train0_remaining_distance / self.train0_speed if self.train0_speed > 0 else 0
        self.train1_remaining_time = self.train1_remaining_distance / self.train1_speed if self.train1_speed > 0 else 0

        # 初始化尾部轨道和位置
        self.train0_tail_track, self.train0_tail_distance = self.calculate_tail_position(
            self.train0_current_track, self.train0_remaining_distance, self.train0_length
        )
        self.train1_tail_track, self.train1_tail_distance = self.calculate_tail_position(
            self.train1_current_track, self.train1_remaining_distance, self.train1_length
        )

        # 统一定时器
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.update_simulation)

        # 绑定按钮
        self.runButton.clicked.connect(self.start_simulation)
        self.pauseButton.clicked.connect(self.stop_simulation)

        # 斜线绘制
        self.line_1G = CustomWidget(self.main_ui.line_1G)
        self.line_8G = CustomWidget(self.main_ui.line_8G)
        self.line_4G = CustomWidget(self.main_ui.line_4G)
        self.line_5G = CustomWidget(self.main_ui.line_5G)

        self.line_1G.setGeometry(self.main_ui.line_1G.geometry())
        self.line_8G.setGeometry(self.main_ui.line_8G.geometry())
        self.line_4G.setGeometry(self.main_ui.line_4G.geometry())
        self.line_5G.setGeometry(self.main_ui.line_5G.geometry())

        self.line_1G.setParent(self)
        self.line_8G.setParent(self)
        self.line_4G.setParent(self)
        self.line_5G.setParent(self)

        self.line_1G.set_line_thickness(4)
        self.line_8G.set_line_thickness(4)
        self.line_4G.set_line_thickness(4)
        self.line_5G.set_line_thickness(4)

        self.line_1G.set_slash_direction(left_slash=False, right_slash=True)
        self.line_8G.set_slash_direction(left_slash=True, right_slash=False)
        self.line_4G.set_slash_direction(left_slash=True, right_slash=False)
        self.line_5G.set_slash_direction(left_slash=False, right_slash=True)

        # 初始化标志位
        self.flag_1g = False
        self.flag_2g = False
        self.flag_3g = False
        self.flag_4g = False
        self.flag_5g = False
        self.flag_6g = False
        self.flag_7g = False
        self.flag_8g = False

        # 初始化轨道电路（每段的低频频率）
        self.low_freq_signal_1g = 29.0
        self.low_freq_signal_2g = 29.0
        self.low_freq_signal_3g = 29.0
        self.low_freq_signal_4g = 29.0
        self.low_freq_signal_5g = 29.0
        self.low_freq_signal_6g = 29.0
        self.low_freq_signal_7g = 29.0
        self.low_freq_signal_8g = 29.0

    def update_simulation_speed(self, value):
        """更新仿真倍速"""
        if value > 0:
            # 加速模式（从 2x 到 11x）
            self.simulation_speed = value + 1
        elif value < 0:
            # 慢速模式（从 1x 到 0.1x）
            self.simulation_speed = 1 / abs(value)
        else:
            # 正常速度（1x）
            self.simulation_speed = 1.0

        # 更新倍速显示
        self.main_ui.acctimeLabel.setText(f"倍速: {self.simulation_speed:.1f}x")

        # 调整定时器间隔
        base_interval = 100  # 基础定时器间隔，单位 ms
        adjusted_interval = int(base_interval / self.simulation_speed)
        if adjusted_interval < 1:  # 确保间隔值不为 0
            adjusted_interval = 1
        self.main_timer.setInterval(adjusted_interval)

    def start_simulation(self):
        """开始仿真，初始化所有参数"""
        # 检查两个轨道选择是否相同
        if self.train0_trackBox.value() == self.train1_trackBox.value():
            QMessageBox.warning(
                self,
                "轨道选择错误",
                "列车 0 和列车 1 不能在同一起始轨道上！"
            )
            return  # 终止函数

        print("开始仿真")
        self.is_paused = False  # 取消暂停状态

        # 初始化列车位置和轨道
        self.train0_current_track = self.train0_trackBox.value()
        self.train1_current_track = self.train1_trackBox.value()

        # 设置列车在当前轨道上的初始位置
        self.train0_position_in_track = float(self.train0_positionEdit.text())  # 获取初始位置
        self.train1_position_in_track = float(self.train1_positionEdit.text())  # 获取初始位置

        # 根据初始位置计算剩余距离
        self.train0_remaining_distance = self.track_length - self.train0_position_in_track
        self.train1_remaining_distance = self.track_length - self.train1_position_in_track

        # 初始化列车速度
        self.train0_speed = float(self.train0_speedEdit.text()) / 3.6  # 转换为 m/s
        self.train1_speed = float(self.train1_speedEdit.text()) / 3.6  # 转换为 m/s

        # 初始化剩余时间
        self.train0_remaining_time = self.train0_remaining_distance / self.train0_speed if self.train0_speed > 0 else 0
        self.train1_remaining_time = self.train1_remaining_distance / self.train1_speed if self.train1_speed > 0 else 0

        # 初始化尾部轨道和位置
        self.train0_tail_track, self.train0_tail_distance = self.calculate_tail_position(
            self.train0_current_track, self.train0_remaining_distance, self.train0_length
        )
        self.train1_tail_track, self.train1_tail_distance = self.calculate_tail_position(
            self.train1_current_track, self.train1_remaining_distance, self.train1_length
        )

        # 根据滑动条值设置倍速
        slider_value = self.accelerateSlider.value()
        self.update_simulation_speed(slider_value)

        self.first_flag = True

        # 启动统一定时器
        self.main_timer.start()

    def stop_simulation(self):
        """暂停或继续仿真"""
        if not self.is_paused:
            print('暂停仿真')
            self.pauseButton.setText('继续仿真')
            self.is_paused = True
            self.main_timer.stop()  # 停止定时器
        elif self.is_paused:
            print('继续仿真')
            self.pauseButton.setText('暂停仿真')
            self.is_paused = False
            self.main_timer.start()

    def update_simulation(self):
        """统一更新仿真逻辑"""
        # 每次定时器触发的时间间隔（秒）
        base_interval = 0.1  # 基础时间间隔，100ms
        time_interval = base_interval * self.simulation_speed  # 根据倍速调整时间间隔

        # 更新列车 0 的位置和剩余距离
        if self.train0_speed > 0 and self.train0_remaining_distance > 0:
            distance_moved = self.train0_speed * time_interval
            self.train0_remaining_distance -= distance_moved
            self.train0_remaining_time = max(self.train0_remaining_distance / self.train0_speed, 0)

            # 列车 0 到达下一轨道时
            if self.train0_remaining_distance <= 0:
                self.train0_current_track += 1
                if self.train0_current_track > 8:  # 循环到 01G
                    self.train0_current_track = 1
                self.train0_remaining_distance += self.track_length  # 将剩余距离累加到下一轨道的距离
                self.train0_remaining_time = self.train0_remaining_distance / self.train0_speed
        elif self.train0_speed == 0:
            # 保持当前位置，不回到区段起点
            self.train0_remaining_time = 0

        # 更新列车 1 的位置和剩余距离
        if self.train1_speed > 0 and self.train1_remaining_distance > 0:
            distance_moved = self.train1_speed * time_interval
            self.train1_remaining_distance -= distance_moved
            self.train1_remaining_time = max(self.train1_remaining_distance / self.train1_speed, 0)

            # 列车 1 到达下一轨道时
            if self.train1_remaining_distance <= 0:
                self.train1_current_track += 1
                if self.train1_current_track > 8:  # 循环到 01G
                    self.train1_current_track = 1
                self.train1_remaining_distance += self.track_length  # 将剩余距离累加到下一轨道的距离
                self.train1_remaining_time = self.train1_remaining_distance / self.train1_speed
        elif self.train1_speed == 0:
            # 保持当前位置，不回到区段起点
            self.train1_remaining_time = 0

        # 更新列车尾部所在的区段号和尾部到下一区段的距离
        self.update_tail_positions()

        # 更新轨道和信号显示
        self.update_train_location()

        # 更新限速和速度控制
        self.speed_control()

        # 更新列车标签
        self.update_train_labels()

        # 更新列车实时速度
        self.update_current_speed_display()

    def calculate_tail_position(self, current_track, remaining_distance, train_length):
        """
        计算列车尾部所在轨道和到尾部的距离
        :param current_track: 列车头部所在轨道编号
        :param remaining_distance: 列车头部到轨道末端的剩余距离
        :param train_length: 列车的总长度
        :return: (尾部轨道编号, 尾部距离到轨道末端的距离)
        """
        tail_distance = remaining_distance + train_length  # 计算尾部到轨道末端的距离

        if tail_distance <= self.track_length:
            # 尾部仍在当前轨道
            return current_track, tail_distance
        else:
            # 尾部跨越到前一个轨道
            tail_distance -= self.track_length
            tail_track = current_track - 1 if current_track > 1 else 8  # 循环回到最后一个轨道
            return tail_track, tail_distance

    def update_tail_positions(self):
        """
        更新列车尾部的轨道编号和剩余距离
        """
        # 更新列车 0 的尾部位置
        self.train0_tail_track, self.train0_tail_distance = self.calculate_tail_position(
            self.train0_current_track, self.train0_remaining_distance, self.train0_length
        )

        # 更新列车 1 的尾部位置
        self.train1_tail_track, self.train1_tail_distance = self.calculate_tail_position(
            self.train1_current_track, self.train1_remaining_distance, self.train1_length
        )

    def update_current_speed_display(self):
        """更新列车当前速度显示"""
        # 将速度从 m/s 转换为 km/h 并显示在 LCD 上
        train0_speed_kmh = self.train0_speed * 3.6  # m/s 转换为 km/h
        train1_speed_kmh = self.train1_speed * 3.6  # m/s 转换为 km/h

        self.train0_nowLabel.setText(f'{train0_speed_kmh:.0f}')
        self.train1_nowLabel.setText(f'{train1_speed_kmh:.0f}')

    def update_train_labels(self):
        """更新列车标签显示"""
        self.train0Label.setText(
            f"列车 0 <br>- 距离 0{self.train0_current_track + 1}G: {self.train0_remaining_distance:.0f} m <br>- 到达时间: {self.train0_remaining_time:.1f} s"
        )
        self.train1Label.setText(
            f"列车 1 <br>- 距离 0{self.train1_current_track + 1}G: {self.train1_remaining_distance:.0f} m <br>- 到达时间: {self.train1_remaining_time:.1f} s"
        )

    def update_train_length(self):
        if self.train0_nounBox.currentIndex() == 0:
            self.train0_length = 209
        elif self.train0_nounBox.currentIndex() == 1:
            self.train0_length = 302
        elif self.train0_nounBox.currentIndex() == 2:
            self.train0_length = 414
        elif self.train0_nounBox.currentIndex() == 3:
            self.train0_length = 440

        if self.train1_nounBox.currentIndex() == 0:
            self.train1_length = 209
        elif self.train1_nounBox.currentIndex() == 1:
            self.train1_length = 302
        elif self.train1_nounBox.currentIndex() == 2:
            self.train1_length = 414
        elif self.train0_nounBox.currentIndex() == 3:
            self.train1_length = 440

    def update_train_location(self):
        # 初始化轨道颜色为默认颜色
        default_color = self.palette().color(self.foregroundRole())
        red_color = QColor("red")

        # 重置所有轨道的默认显示
        self.line_1G.set_custom_color(default_color)
        self.line_2G.setStyleSheet("")
        self.line_3G.setStyleSheet("")
        self.line_4G.set_custom_color(default_color)
        self.line_5G.set_custom_color(default_color)
        self.line_6G.setStyleSheet("")
        self.line_7G.setStyleSheet("")
        self.line_8G.set_custom_color(default_color)

        # 创建一个字典来跟踪轨道上是否有列车（头部或尾部）
        track_status = {i: 0 for i in range(1, 9)}  # 1-8轨道，初始状态为0

        # 更新列车 0 的轨道显示（头部和尾部）
        track_status[self.train0_current_track] += 1
        track_status[self.train0_tail_track] += 1  # 增加尾部对应轨道
        if self.train0_current_track == 1 or self.train0_tail_track == 1:
            self.line_1G.set_custom_color(red_color)
        if self.train0_current_track == 2 or self.train0_tail_track == 2:
            self.line_2G.setStyleSheet("color: red;")
        if self.train0_current_track == 3 or self.train0_tail_track == 3:
            self.line_3G.setStyleSheet("color: red;")
        if self.train0_current_track == 4 or self.train0_tail_track == 4:
            self.line_4G.set_custom_color(red_color)
        if self.train0_current_track == 5 or self.train0_tail_track == 5:
            self.line_5G.set_custom_color(red_color)
        if self.train0_current_track == 6 or self.train0_tail_track == 6:
            self.line_6G.setStyleSheet("color: red;")
        if self.train0_current_track == 7 or self.train0_tail_track == 7:
            self.line_7G.setStyleSheet("color: red;")
        if self.train0_current_track == 8 or self.train0_tail_track == 8:
            self.line_8G.set_custom_color(red_color)

        # 更新列车 1 的轨道显示（头部和尾部）
        track_status[self.train1_current_track] += 1
        track_status[self.train1_tail_track] += 1  # 增加尾部对应轨道
        if self.train1_current_track == 1 or self.train1_tail_track == 1:
            self.line_1G.set_custom_color(red_color)
        if self.train1_current_track == 2 or self.train1_tail_track == 2:
            self.line_2G.setStyleSheet("color: red;")
        if self.train1_current_track == 3 or self.train1_tail_track == 3:
            self.line_3G.setStyleSheet("color: red;")
        if self.train1_current_track == 4 or self.train1_tail_track == 4:
            self.line_4G.set_custom_color(red_color)
        if self.train1_current_track == 5 or self.train1_tail_track == 5:
            self.line_5G.set_custom_color(red_color)
        if self.train1_current_track == 6 or self.train1_tail_track == 6:
            self.line_6G.setStyleSheet("color: red;")
        if self.train1_current_track == 7 or self.train1_tail_track == 7:
            self.line_7G.setStyleSheet("color: red;")
        if self.train1_current_track == 8 or self.train1_tail_track == 8:
            self.line_8G.set_custom_color(red_color)

        # 更新标志位
        self.flag_1g = track_status[1] > 0
        self.flag_2g = track_status[2] > 0
        self.flag_3g = track_status[3] > 0
        self.flag_4g = track_status[4] > 0
        self.flag_5g = track_status[5] > 0
        self.flag_6g = track_status[6] > 0
        self.flag_7g = track_status[7] > 0
        self.flag_8g = track_status[8] > 0

        # 调用低频信号更新
        self.zpw_low_frequency_signal()

    def update_flag_status(self):
        """
        更新每个 flagXLabel 的占用状态，01G 表示轨道号，后续跟随状态变化。
        """
        # 获取所有轨道的占用状态列表
        # 1表示占用，0表示空闲，顺序为1G -> 8G
        track_status = [
            self.flag_1g, self.flag_2g, self.flag_3g, self.flag_4g,
            self.flag_5g, self.flag_6g, self.flag_7g, self.flag_8g
        ]

        for i in range(8):  # 遍历 8 个 flagLabel
            label_text = []
            # 添加轨道号
            track_number = f"{(i + 1):02d}G:"  # 格式化为两位数字
            label_text.append(f'{track_number}<br>')

            for j in range(4):  # 遍历4个轨道
                # 计算当前轨道对应的索引（超过8回到1）
                track_index = (i + j) % 8
                # 判断轨道占用状态，↓ 表示占用，↑ 表示空闲
                status_symbol = '↓' if track_status[track_index] else '↑'
                # 构造显示文本
                label_text.append(f"{j}GJ {status_symbol}")
                # 每 2 条换行
                if (j + 1) % 2 == 0 and j != 3:  # 避免最后多余换行
                    label_text.append("<br>")

            # 将拼接好的文本设置到对应的 Label
            label_name = f"flag{i + 1}Label"  # 对应 flag1Label 到 flag8Label
            getattr(self, label_name).setText(" ".join(label_text))


    def zpw_low_frequency_signal(self):
        # 初始化字典来存储各信号值，默认值为 11.4
        signal_values = {
            "low_freq_signal_1g": 11.4,
            "low_freq_signal_2g": 11.4,
            "low_freq_signal_3g": 11.4,
            "low_freq_signal_4g": 11.4,
            "low_freq_signal_5g": 11.4,
            "low_freq_signal_6g": 11.4,
            "low_freq_signal_7g": 11.4,
            "low_freq_signal_8g": 11.4,
        }

        # 辅助函数：更新信号值并取最大值
        def update_signal(signal_name, value):
            signal_values[signal_name] = max(signal_values[signal_name], value)

        if self.flag_1g:
            update_signal("low_freq_signal_5g", 11.4)  # L
            update_signal("low_freq_signal_6g", 13.6)  # LU
            update_signal("low_freq_signal_7g", 16.9)  # U
            update_signal("low_freq_signal_8g", 29.0)  # H
        if self.flag_2g:
            update_signal("low_freq_signal_6g", 11.4)  # L
            update_signal("low_freq_signal_7g", 13.6)  # LU
            update_signal("low_freq_signal_8g", 16.9)  # U
            update_signal("low_freq_signal_1g", 29.0)  # H
        if self.flag_3g:
            update_signal("low_freq_signal_7g", 11.4)  # L
            update_signal("low_freq_signal_8g", 13.6)  # LU
            update_signal("low_freq_signal_1g", 16.9)  # U
            update_signal("low_freq_signal_2g", 29.0)  # H
        if self.flag_4g:
            update_signal("low_freq_signal_8g", 11.4)  # L
            update_signal("low_freq_signal_1g", 13.6)  # LU
            update_signal("low_freq_signal_2g", 16.9)  # U
            update_signal("low_freq_signal_3g", 29.0)  # H
        if self.flag_5g:
            update_signal("low_freq_signal_1g", 11.4)  # L
            update_signal("low_freq_signal_2g", 13.6)  # LU
            update_signal("low_freq_signal_3g", 16.9)  # U
            update_signal("low_freq_signal_4g", 29.0)  # H
        if self.flag_6g:
            update_signal("low_freq_signal_2g", 11.4)  # L
            update_signal("low_freq_signal_3g", 13.6)  # LU
            update_signal("low_freq_signal_4g", 16.9)  # U
            update_signal("low_freq_signal_5g", 29.0)  # H
        if self.flag_7g:
            update_signal("low_freq_signal_3g", 11.4)  # L
            update_signal("low_freq_signal_4g", 13.6)  # LU
            update_signal("low_freq_signal_5g", 16.9)  # U
            update_signal("low_freq_signal_6g", 29.0)  # H
        if self.flag_8g:
            update_signal("low_freq_signal_4g", 11.4)  # L
            update_signal("low_freq_signal_5g", 13.6)  # LU
            update_signal("low_freq_signal_6g", 16.9)  # U
            update_signal("low_freq_signal_7g", 29.0)  # H

        # 将字典中的值赋给对象属性
        self.low_freq_signal_1g = signal_values["low_freq_signal_1g"]
        self.low_freq_signal_2g = signal_values["low_freq_signal_2g"]
        self.low_freq_signal_3g = signal_values["low_freq_signal_3g"]
        self.low_freq_signal_4g = signal_values["low_freq_signal_4g"]
        self.low_freq_signal_5g = signal_values["low_freq_signal_5g"]
        self.low_freq_signal_6g = signal_values["low_freq_signal_6g"]
        self.low_freq_signal_7g = signal_values["low_freq_signal_7g"]
        self.low_freq_signal_8g = signal_values["low_freq_signal_8g"]

        self.info_line_label()
        self.railway_signal()
        self.update_flag_status()

    def info_line_label(self):
        """更新轨道信息显示"""
        info_template = "<br>低频：{low_freq_signal} Hz<br>载频：{center_freq} Hz"
        center_freqs = [2301.4, 1698.2, 2298.7, 1701.4] * 2  # 循环中心频率
        for i in range(8):
            getattr(self, f"info{i + 1}Label").setText(
                f"0{i + 1}G:" + info_template.format(
                    low_freq_signal=getattr(self, f"low_freq_signal_{i + 1}g"),
                    center_freq=center_freqs[i],
                )
            )

    def railway_signal(self):
        # 定义一个映射关系，用于根据信号值设置 LED 样式
        signal_styles = {
            11.4: ("green", "gray"),  # L
            13.6: ("green", "yellow"),  # LU
            16.9: ("gray", "yellow"),  # U
            29.0: ("red", "gray"),  # H
        }

        # 辅助函数：设置 LED 样式
        def set_led_style(signal_value, led_1, led_2):
            if signal_value in signal_styles:
                color1, color2 = signal_styles[signal_value]
                led_1.setStyleSheet(f"QPushButton{{border-radius: 10px;background-color: {color1};}}")
                led_2.setStyleSheet(f"QPushButton{{border-radius: 10px;background-color: {color2};}}")
            else:
                # 如果信号值未定义，默认设置为关闭状态
                led_1.setStyleSheet("QPushButton{border-radius: 10px;background-color: gray;}")
                led_2.setStyleSheet("QPushButton{border-radius: 10px;background-color: gray;}")

        # 设置所有低频信号的 LED 状态
        set_led_style(self.low_freq_signal_8g, self.led_x11, self.led_x12)
        set_led_style(self.low_freq_signal_1g, self.led_x21, self.led_x22)
        set_led_style(self.low_freq_signal_2g, self.led_x31, self.led_x32)
        set_led_style(self.low_freq_signal_3g, self.led_x41, self.led_x42)
        set_led_style(self.low_freq_signal_4g, self.led_x51, self.led_x52)
        set_led_style(self.low_freq_signal_5g, self.led_x61, self.led_x62)
        set_led_style(self.low_freq_signal_6g, self.led_x71, self.led_x72)
        set_led_style(self.low_freq_signal_7g, self.led_x81, self.led_x82)

        self.speed_control()

    def speed_control(self):
        """
        根据列车头部的低频信号动态调整速度。
        """
        # 定义低频信号对应的速度限制 (km/h)
        speed_limits = {
            11.4: None,  # 无限速
            13.6: 160,  # 限速 160 km/h
            16.9: 80,  # 限速 80 km/h
            29.0: 0  # 紧急停车
        }

        # 定义低频信号对应的减速度 (m/s^2)
        deceleration_limits = {
            11.4: 0.5,  # 无限速时的减速度
            13.6: 0.8,  # 限速 160 km/h 时的减速度
            16.9: 1.2,  # 限速 80 km/h 时的减速度
            29.0: 2.5  # 紧急停车的减速度
        }

        # 定义统一的加速度 (m/s^2)
        acceleration = 1.28  # 加速度

        # 时间步长 (秒)，与 `update_simulation` 的间隔一致
        time_step = 0.1

        def get_target_speed(signal, current_speed, initial_speed):
            """
            根据信号计算目标速度
            :param signal: 当前轨道的低频信号
            :param current_speed: 当前速度 (m/s)
            :param initial_speed: 初始速度 (m/s)
            :return: 目标速度 (m/s)
            """
            if signal == 29.0:  # 紧急停车
                return 0
            elif signal == 11.4:  # 无限速
                return initial_speed
            else:
                # 限速转换为 m/s
                limit_speed = speed_limits[signal] / 3.6
                return min(limit_speed, initial_speed)

        def get_deceleration(signal):
            """
            获取对应信号的减速度
            :param signal: 当前轨道的低频信号
            :return: 对应的减速度 (m/s^2)
            """
            return deceleration_limits.get(signal, 0.5)  # 默认减速度为 0.5 m/s^2

        # 调整列车 0 的速度
        train0_signal = getattr(self, f"low_freq_signal_{self.train0_current_track}g")  # 获取列车 0 头部信号
        train0_initial_speed = float(self.train0_speedEdit.text()) / 3.6  # 初始速度 (m/s)

        train0_target_speed = get_target_speed(train0_signal, self.train0_speed, train0_initial_speed)
        train0_deceleration = get_deceleration(train0_signal)

        # 如果初始速度高于限速值，直接设置为限速
        if self.train0_speed > train0_target_speed and self.train0_speed == train0_initial_speed and self.first_flag:
            self.train0_speed = train0_target_speed
        else:
            if self.train0_speed > train0_target_speed:
                # 减速
                self.train0_speed = max(self.train0_speed - train0_deceleration * time_step, train0_target_speed)
            elif self.train0_speed < train0_target_speed:
                # 加速
                self.train0_speed = min(self.train0_speed + acceleration * time_step, train0_target_speed)

        # 调整列车 1 的速度
        train1_signal = getattr(self, f"low_freq_signal_{self.train1_current_track}g")  # 获取列车 1 头部信号
        train1_initial_speed = float(self.train1_speedEdit.text()) / 3.6  # 初始速度 (m/s)

        train1_target_speed = get_target_speed(train1_signal, self.train1_speed, train1_initial_speed)
        train1_deceleration = get_deceleration(train1_signal)

        # 如果初始速度高于限速值，直接设置为限速
        if self.train1_speed > train1_target_speed and self.train1_speed == train1_initial_speed and self.first_flag:
            self.train1_speed = train1_target_speed
        else:
            if self.train1_speed > train1_target_speed:
                # 减速
                self.train1_speed = max(self.train1_speed - train1_deceleration * time_step, train1_target_speed)
            elif self.train1_speed < train1_target_speed:
                # 加速
                self.train1_speed = min(self.train1_speed + acceleration * time_step, train1_target_speed)

        self.first_flag = False

        # 更新限速显示
        train0_limit_kmh = train0_target_speed * 3.6  # 转换为 km/h
        train1_limit_kmh = train1_target_speed * 3.6  # 转换为 km/hs

        # 如果信号为无限速（11.4），显示列车设置的最高时速
        self.train0_limitLabel.setText(
            f'{round(train0_limit_kmh, 0):.0f}' if train0_signal != 11.4 else f'{round(train0_initial_speed * 3.6, 0):.0f}'
        )
        self.train1_limitLabel.setText(
            f'{round(train1_limit_kmh, 0):.0f}' if train1_signal != 11.4 else f'{round(train1_initial_speed * 3.6, 0):.0f}'
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_ui = mainUi()
    main_ui.show()
    sys.exit(app.exec())
