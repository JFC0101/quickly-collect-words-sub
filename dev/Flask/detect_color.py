import cv2
import numpy as np

def calculate_overlap(box1, box2): #此函數計算兩個矩形框的重疊比率
    x1_min, y1_min, x1_max, y1_max = box1 #box1 和 box2 各自有四個邊界點 (x_min, y_min, x_max, y_max)
    x2_min, y2_min, x2_max, y2_max = box2

    overlap_x_min = max(x1_min, x2_min) #重疊區域的左上角點取兩個矩形框左上角的最大值 (overlap_x_min, overlap_y_min)。
    overlap_y_min = max(y1_min, y2_min)
    overlap_x_max = min(x1_max, x2_max) #重疊區域的右下角點取兩個矩形框右下角的最小值 (overlap_x_max, overlap_y_max)。
    overlap_y_max = min(y1_max, y2_max)

    overlap_area = max(0, overlap_x_max - overlap_x_min) * max(0, overlap_y_max - overlap_y_min) #overlap_area 是重疊區域的面積。

    area1 = (x1_max - x1_min) * (y1_max - y1_min) #area1 和 area2 分別是兩個矩形框的面積。
    area2 = (x2_max - x2_min) * (y2_max - y2_min)

    overlap_ratio1 = overlap_area / area1 if area1 > 0 else 0 #overlap_ratio1 是重疊區域相對於 box1 的比率。
    overlap_ratio2 = overlap_area / area2 if area2 > 0 else 0 #overlap_ratio2 是重疊區域相對於 box2 的比率。

    return max(overlap_ratio1, overlap_ratio2) #返回 overlap_ratio1 和 overlap_ratio2 中的最大值。



def calculate_distance(box1, box2): #此函數計算兩個矩形框中心點之間的歐氏距離。
    x1_min, y1_min, x1_max, y1_max = box1 #center_x1 和 center_y1 是 box1 的中心點。
    x2_min, y2_min, x2_max, y2_max = box2

    center_x1 = (x1_min + x1_max) / 2
    center_y1 = (y1_min + y1_max) / 2
    center_x2 = (x2_min + x2_max) / 2
    center_y2 = (y2_min + y2_max) / 2

    distance = np.sqrt((center_x1 - center_x2) ** 2 + (center_y1 - center_y2) ** 2)
    return distance  #兩個中心點之間的距離。

#此函數將一組矩形框進行合併，如果它們之間的重疊比率超過閾值或中心點距離小於閾值
def merge_rects(rects, overlap_threshold=0.5, distance_threshold=50): 
    merged = [] #merged 用於存儲合併後的矩形框。
    while rects: #從 rects 列表中取出第一個矩形框 r，計算其右下角點 x2 和 y2，並設置為 merged_rect。
        r = rects.pop(0)
        x, y, w, h = r
        x2, y2 = x + w, y + h
        merged_rect = (x, y, x2, y2)

        for other in rects[:]:
            ox, oy, ow, oh = other
            ox2, oy2 = ox + ow, oy + oh
            other_rect = (ox, oy, ox2, oy2)

#如果 merged_rect 和 other_rect 之間的重疊比率超過 overlap_threshold 或中心點距離小於 distance_threshold，則合併它們。
            if calculate_overlap(merged_rect, other_rect) > overlap_threshold or calculate_distance(merged_rect, other_rect) < distance_threshold:
                nx = min(x, ox)
                ny = min(y, oy)
                nx2 = max(x2, ox2)
                ny2 = max(y2, oy2)
                merged_rect = (nx, ny, nx2, ny2)
                rects.remove(other)
        
        merged.append((merged_rect[0], merged_rect[1], merged_rect[2] - merged_rect[0], merged_rect[3] - merged_rect[1]))
    return merged

def detect_color_regions(image_path):
    # 加載圖片
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image not found or unable to load.")
        return []

    # 轉換成 HSV 色彩空間
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 定義顏色範圍
    lower_light = np.array([0, 80, 150])  # 亮色的下界
    upper_light = np.array([180, 255, 255])  # 亮色的上界

    # 創建亮色遮罩
    mask_light = cv2.inRange(hsv_image, lower_light, upper_light)

    # 將亮色遮罩應用到原始圖片上
    processed_image = cv2.bitwise_and(image, image, mask=mask_light)

    # 查找輪廓
    contours, _ = cv2.findContours(mask_light, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 獲取每個輪廓的邊界框座標（x, y, w, h）
    rects = [cv2.boundingRect(contour) for contour in contours]

    # 合併相近或重疊的框框
    merged_rects = merge_rects(rects, overlap_threshold=0.1, distance_threshold=60)

    # 確保所有相近或重疊框框都被合併，最多進行 3 次合併
    for _ in range(3):
        merged_rects = merge_rects(merged_rects, overlap_threshold=0.1, distance_threshold=50)

    # 打印並繪製每個合併後的邊界框座標（xyxy）
    merged_rects_all=[]
    for rect in merged_rects:
        x, y, w, h = rect
        x2, y2 = x + w, y + h       
        
        merged_rects_all.append((x,y,x2,y2))

        #print(f"Merged region: ({x}, {y}, {x2}, {y2})")
        
    #print("Merged regions:", merged_rects_all)
    return merged_rects_all
    


if __name__ == "__main__":
    image_path = 'static/uploads/test10.jpg'
    merged_regions = detect_color_regions(image_path)
    