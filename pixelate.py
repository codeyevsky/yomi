from PIL import Image
import os

def pixelate_image_logic(image_path, output_dir, resolutions):
    processed_images = []
    try:
        img = Image.open(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        original_width, original_height = img.size
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for res in resolutions:
            small_img = img.resize((res, res), resample=Image.Resampling.NEAREST)
            pixelated_img = small_img.resize((original_width, original_height), resample=Image.Resampling.NEAREST)
            output_file = os.path.join(output_dir, f"{base_name}_pixelated_{res}x{res}.png")
            
            pixelated_img.save(output_file)
            processed_images.append(output_file)
            
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return []
    
    return processed_images