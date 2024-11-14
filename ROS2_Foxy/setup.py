from setuptools import setup, find_packages

package_name = 'fair_drip'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'PyQt5', 'pandas', 'websockets'],
    zip_safe=True,
    maintainer='bst',
    maintainer_email='beanst_hwangsh@naver.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'fair_lis = fair_drip.Ros2_Listener_Robot:main',
            'talker = fair_drip.ros2_bridgesever_test:main',
            'robot_test = fair_drip.robot_test:main', 
        ],
    },
    package_data={
        'fair_drip': ['fair_drip/*.ui',
                      'fair_drip/Set_Value.yaml',
                      'fair_drip/frrpc.so']
    },
)
