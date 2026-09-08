import math
from pathlib import Path


# =========================================================
# PİST AYARLARI
# =========================================================

# Düz bölümlerin pist merkezinden sağa/sola uzandığı mesafe.
# Üst ve alt düz bölümlerin toplam uzunluğu bunun iki katıdır.
STRAIGHT_HALF_LENGTH = 4.0

# İki uçtaki yarım dairelerin yarıçapı
CURVE_RADIUS = 3.0

# Yolun toplam genişliği
ROAD_WIDTH = 2.4

# Yolun kenar çizgilerinin genişliği
EDGE_LINE_WIDTH = 0.10

# Ortadaki kesik çizginin genişliği
CENTER_LINE_WIDTH = 0.08

# Her düz bölüm ve her yarım daire için kullanılacak parça sayısı
SECTION_SEGMENT_COUNT = 60


# =========================================================
# DOSYA KONUMU
# =========================================================

script_directory = Path(__file__).resolve().parent
package_directory = script_directory.parent
worlds_directory = package_directory / 'worlds'
output_file = worlds_directory / 'oval_track.world'


# Oluşturulan SDF satırlarını bu listeye ekleyeceğiz
lines = []


def add_line(text):
    """Verilen metni oluşturulacak dünya dosyasına ekler."""
    lines.append(text)


def add_visual(
    name,
    x,
    y,
    z,
    length,
    width,
    height,
    yaw,
    color
):
    """Gazebo dünyasına görünen bir kutu ekler."""
    add_line(f'                <visual name="{name}">')
    add_line(
        f'                    <pose>'
        f'{x:.4f} {y:.4f} {z:.4f} 0 0 {yaw:.4f}'
        f'</pose>'
    )
    add_line('                    <geometry>')
    add_line('                        <box>')
    add_line(
        f'                            <size>'
        f'{length:.4f} {width:.4f} {height:.4f}'
        f'</size>'
    )
    add_line('                        </box>')
    add_line('                    </geometry>')
    add_line('                    <material>')
    add_line(f'                        <ambient>{color}</ambient>')
    add_line(f'                        <diffuse>{color}</diffuse>')
    add_line('                    </material>')
    add_line('                </visual>')


def add_collision(
    name,
    x,
    y,
    z,
    length,
    width,
    height,
    yaw
):
    """Gazebo fizik motoru için çarpışma kutusu ekler."""
    add_line(f'                <collision name="{name}">')
    add_line(
        f'                    <pose>'
        f'{x:.4f} {y:.4f} {z:.4f} 0 0 {yaw:.4f}'
        f'</pose>'
    )
    add_line('                    <geometry>')
    add_line('                        <box>')
    add_line(
        f'                            <size>'
        f'{length:.4f} {width:.4f} {height:.4f}'
        f'</size>'
    )
    add_line('                        </box>')
    add_line('                    </geometry>')
    add_line('                </collision>')


# =========================================================
# DÜNYA DOSYASININ BAŞLANGICI
# =========================================================

add_line('<?xml version="1.0"?>')
add_line('')
add_line('<sdf version="1.6">')
add_line('')
add_line('    <world name="oval_track_world">')
add_line('')
add_line('        <!-- Gazebo ortamındaki ışık -->')
add_line('        <include>')
add_line('            <uri>model://sun</uri>')
add_line('        </include>')
add_line('')
add_line('        <!-- Genel zemin -->')
add_line('        <include>')
add_line('            <uri>model://ground_plane</uri>')
add_line('        </include>')
add_line('')
add_line('        <!-- Oval pistin bütün parçaları -->')
add_line('        <model name="oval_track">')
add_line('            <static>true</static>')
add_line('')
add_line('            <link name="track_link">')


# =========================================================
# KOŞU PİSTİNİN MERKEZ HATTINI OLUŞTUR
# =========================================================

track_points = []

# Üst düz bölüm: sağdan sola
for index in range(SECTION_SEGMENT_COUNT):
    ratio = index / SECTION_SEGMENT_COUNT
    x = STRAIGHT_HALF_LENGTH * (1.0 - 2.0 * ratio)
    track_points.append((x, CURVE_RADIUS))

# Sol yarım daire: üstten alta
for index in range(SECTION_SEGMENT_COUNT):
    angle = (
        math.pi / 2.0
        + math.pi * index / SECTION_SEGMENT_COUNT
    )
    x = -STRAIGHT_HALF_LENGTH + CURVE_RADIUS * math.cos(angle)
    y = CURVE_RADIUS * math.sin(angle)
    track_points.append((x, y))

# Alt düz bölüm: soldan sağa
for index in range(SECTION_SEGMENT_COUNT):
    ratio = index / SECTION_SEGMENT_COUNT
    x = -STRAIGHT_HALF_LENGTH + 2.0 * STRAIGHT_HALF_LENGTH * ratio
    track_points.append((x, -CURVE_RADIUS))

# Sağ yarım daire: alttan üste
for index in range(SECTION_SEGMENT_COUNT):
    angle = (
        -math.pi / 2.0
        + math.pi * index / SECTION_SEGMENT_COUNT
    )
    x = STRAIGHT_HALF_LENGTH + CURVE_RADIUS * math.cos(angle)
    y = CURVE_RADIUS * math.sin(angle)
    track_points.append((x, y))


# =========================================================
# PİST PARÇALARINI OLUŞTUR
# =========================================================

for index in range(len(track_points)):

    # Parçanın başlangıç ve bitiş noktaları
    x_1, y_1 = track_points[index]
    x_2, y_2 = track_points[(index + 1) % len(track_points)]

    # Başlangıç ve bitiş noktalarının tam ortası
    center_x = (x_1 + x_2) / 2.0
    center_y = (y_1 + y_2) / 2.0

    # İki nokta arasındaki fark
    difference_x = x_2 - x_1
    difference_y = y_2 - y_1

    # Yol parçasının uzunluğu
    base_length = math.hypot(
        difference_x,
        difference_y
    )

    # Küçük boşluklar oluşmaması için parçayı biraz uzat
    segment_length = base_length * 1.10

    # Yol parçasının dönmesi gereken açı
    yaw = math.atan2(
        difference_y,
        difference_x
    )

    # Yolun ilerleme yönündeki birim vektör
    tangent_x = difference_x / base_length
    tangent_y = difference_y / base_length

    # İlerleme yönüne dik olan vektör
    normal_x = -tangent_y
    normal_y = tangent_x

    # Kenar çizgilerinin yol merkezine uzaklığı
    edge_offset = (
        ROAD_WIDTH / 2.0
        - EDGE_LINE_WIDTH / 2.0
    )

    # Sol kenar çizgisinin merkezi
    left_line_x = center_x + normal_x * edge_offset
    left_line_y = center_y + normal_y * edge_offset

    # Sağ kenar çizgisinin merkezi
    right_line_x = center_x - normal_x * edge_offset
    right_line_y = center_y - normal_y * edge_offset

    # Koyu renkli yolun görünen kısmı
    add_visual(
        name=f'road_visual_{index}',
        x=center_x,
        y=center_y,
        z=0.025,
        length=segment_length,
        width=ROAD_WIDTH,
        height=0.05,
        yaw=yaw,
        color='0.08 0.08 0.08 1'
    )

    # Yolun fiziksel çarpışma kısmı
    add_collision(
        name=f'road_collision_{index}',
        x=center_x,
        y=center_y,
        z=0.025,
        length=segment_length,
        width=ROAD_WIDTH,
        height=0.05,
        yaw=yaw
    )

    # Sol beyaz sınır çizgisi
    add_visual(
        name=f'left_edge_line_{index}',
        x=left_line_x,
        y=left_line_y,
        z=0.055,
        length=segment_length,
        width=EDGE_LINE_WIDTH,
        height=0.01,
        yaw=yaw,
        color='1 1 1 1'
    )

    # Sağ beyaz sınır çizgisi
    add_visual(
        name=f'right_edge_line_{index}',
        x=right_line_x,
        y=right_line_y,
        z=0.055,
        length=segment_length,
        width=EDGE_LINE_WIDTH,
        height=0.01,
        yaw=yaw,
        color='1 1 1 1'
    )

    # Her iki parçadan yalnızca birine orta çizgi koy.
    # Böylece kesik çizgi görünümü oluşur.
    if index % 2 == 0:

        add_visual(
            name=f'center_line_{index}',
            x=center_x,
            y=center_y,
            z=0.056,
            length=segment_length * 0.60,
            width=CENTER_LINE_WIDTH,
            height=0.012,
            yaw=yaw,
            color='1 0.8 0 1'
        )


# =========================================================
# DÜNYA DOSYASINI KAPAT
# =========================================================

add_line('            </link>')
add_line('')
add_line('        </model>')
add_line('')
add_line('    </world>')
add_line('')
add_line('</sdf>')


# =========================================================
# OLUŞTURULAN DOSYAYI KAYDET
# =========================================================

worlds_directory.mkdir(
    parents=True,
    exist_ok=True
)

output_file.write_text(
    '\n'.join(lines) + '\n',
    encoding='utf-8'
)

print('Oval pist başarıyla oluşturuldu.')
print(f'Dosya konumu: {output_file}')
