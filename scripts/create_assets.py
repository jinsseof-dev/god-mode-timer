import os
from PIL import Image, ImageDraw

def create_icon(size):
    """주어진 크기에 맞춰 번개 아이콘 이미지를 생성합니다."""
    # 투명 배경 이미지 생성
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 배경 원 그리기 (다크 그레이 - 번개를 돋보이게 함)
    bg_margin = size * 2 / 64
    bg_bbox = (bg_margin, bg_margin, size - bg_margin, size - bg_margin)
    draw.ellipse(bg_bbox, fill="#333333", outline="#555555")
    
    # 64x64 기준 번개 좌표
    points_base = [
        (36, 4), (20, 34), (32, 34), 
        (16, 60), (48, 26), (36, 26)
    ]
    
    # 크기에 맞게 좌표 변환
    points = []
    for x, y in points_base:
        points.append((x * size / 64, y * size / 64))
    
    # 윤곽선 두께 (최소 1픽셀)
    outline_width = max(1, int(size * 2 / 64))
    
    # 번개 그리기 (골드)
    draw.polygon(points, fill="#FFD700", outline="#B8860B", width=outline_width)
    
    return image

def main():
    # 저장할 폴더 경로 설정 (scripts 폴더 상위 -> store_package/Assets)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    assets_dir = os.path.join(project_root, "store_package", "Assets")
    
    # 폴더가 없으면 생성
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"📁 폴더 생성됨: {assets_dir}")
        
    # 윈도우 스토어 필수 아이콘 목록 (파일명: 크기)
    assets = {
        "StoreLogo.png": 50,
        "Square150x150Logo.png": 150,
        "Square44x44Logo.png": 44
    }
    
    print("🎨 이미지 자산 생성 중...")
    for filename, size in assets.items():
        img = create_icon(size)
        save_path = os.path.join(assets_dir, filename)
        img.save(save_path)
        print(f"✅ 저장 완료: {filename} ({size}x{size})")
        
    print("\n🎉 모든 이미지가 'store_package/Assets' 폴더에 준비되었습니다!")

if __name__ == "__main__":
    main()