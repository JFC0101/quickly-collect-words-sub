import os
# 加载凭证
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'static\key (do not upload)\google-ai-class-project_api-key.json'
import io
import cv2
import numpy as np
from google.cloud import vision
from google.cloud.vision_v1 import types
from detect_color import detect_color_regions


def calculate_overlap_1(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    overlap_x_min = max(x1_min, x2_min)
    overlap_y_min = max(y1_min, y2_min)
    overlap_x_max = min(x1_max, x2_max)
    overlap_y_max = min(y1_max, y2_max)

    overlap_area = max(0, overlap_x_max - overlap_x_min) * max(0, overlap_y_max - overlap_y_min)

    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)

    overlap_ratio1 = overlap_area / area1 if area1 > 0 else 0
    overlap_ratio2 = overlap_area / area2 if area2 > 0 else 0

    return max(overlap_ratio1, overlap_ratio2), overlap_area / min(area1, area2)

def detect_text(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    ocr_boxes = []

    for i, text in enumerate(texts):
        if i == 0:
            continue  # 跳過第一個大框框
        vertices = ([(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices])
        x_min = min(vertex[0] for vertex in vertices)
        y_min = min(vertex[1] for vertex in vertices)
        x_max = max(vertex[0] for vertex in vertices)
        y_max = max(vertex[1] for vertex in vertices)
        ocr_boxes.append((x_min, y_min, x_max, y_max, text.description))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(response.error.message))
    
    return ocr_boxes

#增加图像对比度并保存处理后的图像
    """
    参数:
    - image_path: 输入图像的路径
    - output_path: 输出处理后图像的路径
    - alpha: 对比度控制 (0-3.0) 越大對比越強
    - beta: 亮度控制 (0-100) 越大越亮
    - saturation_scale: 彩度控制 (1.0-3.0) 彩度参数通常不会引起过曝问题
    - sharpening_factor: 锐利度控制 (1.0-3.0)
    """
def increase_contrast(image_path, output_path, alpha=0.8, beta=0, saturation_scale=1.5, sharpening_factor=1.1):

    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image not found or unable to load.")
        return

    # 调整对比度和亮度
    adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    # 调整彩度
    hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV)
    hsv[...,1] = cv2.multiply(hsv[...,1], saturation_scale)
    saturated = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # 调整锐利度
    kernel = np.array([[0, -1, 0], [-1, 5 + sharpening_factor, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(saturated, -1, kernel)

    # 保存处理后的图像
    cv2.imwrite(output_path, sharpened)
    print(f"Image saved to {output_path}")


    return output_path


def process_image(image_path):
    # 讀取圖片

    
    image_cv = cv2.imread(image_path)
    if image_cv is None:
        print("Error: Image not found or unable to load.")
        return []
    
    contrast_image_path = increase_contrast(image_path, 'static/uploads/for_ocr.jpg')

    # 進行文字檢測
    ocr_boxes = detect_text(contrast_image_path)

    # 指定的合併區域
    merged_regions_all = detect_color_regions(image_path)
    print("Merged regions_all", merged_regions_all)

    # 調暗背景
    overlay = image_cv.copy()
    overlay = cv2.addWeighted(image_cv, 0.6, np.zeros_like(image_cv), 0.8, 0)

    result_image = overlay.copy()
    mask = np.zeros_like(image_cv, dtype=np.uint8)

    detected_words = []

    # 檢查合併後的框框和 OCR 框框是否重疊，並抓取單字
    for merged_region in merged_regions_all:
        x, y, x2, y2 = merged_region
        for ocr_box in ocr_boxes:
            x_min, y_min, x_max, y_max, text = ocr_box
            _, min_overlap_ratio = calculate_overlap_1((x, y, x2, y2), (x_min, y_min, x_max, y_max))
            if min_overlap_ratio >= 0.4:
                print(f"Detected word: {text} in region: ({x_min}, {y_min}, {x_max}, {y_max})")
                if text not in detected_words:  # 仅在单词未被检测到时添加
                    detected_words.append(text)
                    # 在原圖上繪製綠色邊界框
                    cv2.rectangle(result_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(result_image, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    # 在掩模圖像上繪製白色邊界框
                    cv2.rectangle(mask, (x_min, y_min), (x_max, y_max), (255, 255, 255), -1)

    # 使用掩模將原圖加亮部分與調暗背景結合
    result_image = cv2.bitwise_and(image_cv, mask) + cv2.bitwise_and(overlay, cv2.bitwise_not(mask))

    # 儲存處理後的圖片
    output_path = 'static/uploads/detect-ocr.jpg'
    cv2.imwrite(output_path, result_image)

    print(f"Processed image saved to {output_path}")

    return detected_words, ocr_boxes

'''
# 調用函數處理圖片並獲取單字列表
image_path = 'static/uploads/test10.jpg'
detected_words = process_image(image_path)
print("Word list:", detected_words)
'''