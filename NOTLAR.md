cd /home/lviv/serit_takip
colcon build --symlink-install
source install/setup.bash
ros2 run my_robot_controller my_first_node

---------------------


Xacro kontrolü başarılıysa:
colcon build --symlink-install --packages-select my_robot_description
Başarılı derlemenin sonunda:
Summary: 1 package finished
görmelisin.
Paketi terminale yeniden tanıt:
source install/setup.bash
Simülasyonu aç:
ros2 launch my_robot_description simulation.launch.py

------------------------------

Şimdi aracı hareket ettirebilirsin.
İleri sürmek için:
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.3}, angular: {z: 0.0}}"
Komut çalıştığı sürece araç ileri gitmelidir. Durdurmak için:
Ctrl+C
Ardından kesin durma komutu gönder:
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0}, angular: {z: 0.0}}"
Sola dönerek ilerlemek için:
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.3}, angular: {z: 0.5}}"
Sağa dönerek ilerlemek için:
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.3}, angular: {z: -0.5}}"
Geri gitmek için:
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: -0.3}, angular: {z: 0.0}}"


-----------------------------
