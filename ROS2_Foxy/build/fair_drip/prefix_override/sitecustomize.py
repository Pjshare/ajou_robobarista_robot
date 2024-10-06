import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/root/ros2_ws/src/Ajou_Drip_Project/ROS2_Foxy/install/fair_drip'
