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
cd /home/lviv/serit_takip
colcon build --symlink-install
source install/setup.bash
ros2 launch my_robot_description simulation.launch.py

-----------------------

Yeni terminalde önce ROS 2 ortamını tanıt:
cd /home/lviv/serit_takip
source install/setup.bash
Sonra klavye kontrol programını çalıştır:
ros2 run teleop_twist_keyboard teleop_twist_keyboard
Bu program klavyeden aldığı komutları /cmd_vel topic’ine gönderir. Araç da bu topic’i dinleyerek hareket eder.

--------------------------------------------

OpenCV, bilgisayarın görüntüleri işlemesini sağlayan bir yazılım kütüphanesidir. Açılımı Open Source Computer Vision Library’dir.
Bizim projemizde kamera görüntüsüne bakıp şeritleri bulmak için kullanacağız.
Örneğin OpenCV ile:
- Kamera görüntüsünü açabiliriz.
- Görüntüyü siyah-beyaz yapabiliriz.
- Sarı ve beyaz şeritleri renklerine göre ayırabiliriz.
- Çizgilerin konumunu bulabiliriz.
- Şeridin merkezinin aracın sağında mı solunda mı olduğunu hesaplayabiliriz.

-----------------

Basitçe:
- ROS: Görüntüyü kameradan kodumuza getirir.
- cv_bridge: Görüntüyü OpenCV’ye uygun hâle çevirir.
- OpenCV: Görüntünün içindeki yolu ve şeritleri inceler.

--------------------------

1. ✅ **Kamera ve görüntü hazırlama:** ROS görüntüsünü `cv_bridge` ile OpenCV’ye çevirme ve yolun alt yarısını ROI olarak seçme.

2. ⏳ **Şeritleri ayırma:** HSV ile sarı/beyaz renkleri filtreleme ve Canny Edge ile kenarları çıkarma.

3. **Şerit doğrularını bulma:** Hough Transform ile sol ve sağ şeritleri tespit edip görüntü üzerinde renkli çizme.

4. **Sapma ve direksiyon hesabı:** Şerit merkezini bulma, görüntü merkezine göre piksel hatasını hesaplama ve P-Controller ile direksiyon değerine dönüştürme.

5. **Otomatik sürüş:** İleri hız ve dönüş komutlarını `/cmd_vel` üzerinden yayınlama, şerit kaybolduğunda durma ve oval pistte test etme.

----------------------------

source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard

---------------------------------

importlar

class CameraNode(Node):

    def __init__(self):
        # Başlangıç ayarları

    def average_line(...):
        # Şerit doğrusu bulma

    def smooth_line(...):
        # Titreşimi azaltma

    def image_callback(...):
        # Kamera görüntüsü geldiğinde çalışan ana bölüm


--------------------------------------

İki şerit görünüyorsa:
    şerit genişliğini ölç ve kaydet

Sonraki karede yalnızca beyaz görünüyorsa:
    son bilinen şerit genişliğiyle şerit merkezini tahmin et

Yalnızca sarı görünüyorsa:
    yine son bilinen genişlikle merkezi tahmin et

İkisi de görünmüyorsa:
    robotu durdur


--------------------------------    