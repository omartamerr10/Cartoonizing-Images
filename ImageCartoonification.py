import torch
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
import pygad
import mediapipe as mp
import os

# ==========================
# Cartoonizer with tunable parameters
# ==========================
def clean_and_soft_cartoonizer(img_path, cartoon_path, saturation_boost=1.4, sharpness_factor=2.1, contrast_factor=1.5):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    gan_model = torch.hub.load(
        "bryandlee/animegan2-pytorch",
        "generator",
        pretrained="face_paint_512_v2",
        device=device
    ).eval()

    img = Image.open(img_path).convert("RGB")
    original_size = img.size
    processed_img = img.resize((512, 512), Image.LANCZOS)
    processed_img = processed_img.filter(ImageFilter.MedianFilter(size=3))
    processed_img = ImageEnhance.Sharpness(processed_img).enhance(sharpness_factor)
    processed_img = ImageEnhance.Contrast(processed_img).enhance(contrast_factor)

    tensor = torch.from_numpy(np.array(processed_img).astype(np.float32) / 127.5 - 1.0
        ).permute(2, 0, 1).unsqueeze(0).to(device)

    with torch.no_grad():
        output = gan_model(tensor)[0].clamp(-1, 1)

    output = (output.permute(1, 2, 0).cpu().numpy() + 1.0) * 127.5
    output = np.clip(output, 0, 255).astype(np.uint8)
    cartoon = Image.fromarray(output).resize(original_size, Image.LANCZOS)

    cartoon_cv = cv2.cvtColor(np.array(cartoon), cv2.COLOR_RGB2BGR)
    cartoon_cv = cv2.bilateralFilter(cartoon_cv, d=9, sigmaColor=50, sigmaSpace=50)
    cartoon = Image.fromarray(cv2.cvtColor(cartoon_cv, cv2.COLOR_BGR2RGB))

    cartoon = cartoon.filter(ImageFilter.SMOOTH_MORE)
    cartoon = cartoon.filter(ImageFilter.EDGE_ENHANCE)
    cartoon = ImageEnhance.Color(cartoon).enhance(saturation_boost)
    cartoon = ImageEnhance.Sharpness(cartoon).enhance(1.1)

    cartoon.save(cartoon_path)
    return cartoon_path

# ==========================
# Exaggeration
# ==========================
def warp_region(img, center, scale=1.2, radius=30):
    h, w = img.shape[:2]
    map_y, map_x = np.indices((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = x - center[0]
            dy = y - center[1]
            distance = np.sqrt(dx*dx + dy*dy)
            if distance < radius:
                factor = (1 - distance / radius) * (scale - 1)
                map_x[y, x] = x + dx * factor
                map_y[y, x] = y + dy * factor
    return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def get_region_center(points, indices):
    coords = points[indices]
    center = np.mean(coords, axis=0).astype(int)
    return tuple(center)

def exaggerate_features(image_path, output_path, eye_scale=0.8, ear_scale=1.1, nose_scale=1.1):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        print("❌ No face detected.")
        return None

    landmarks = results.multi_face_landmarks[0]
    points = np.array([[int(p.x * w), int(p.y * h)] for p in landmarks.landmark])

    left_eye_center = get_region_center(points, [33, 133, 159, 145, 160, 158])
    right_eye_center = get_region_center(points, [263, 362, 387, 373, 380, 385])
    nose_center = get_region_center(points, [152, 148, 377, 400, 378, 379])
    face_outline_center = get_region_center(points, list(range(0, 17)))
    left_ear_center = get_region_center(points, [234, 93, 132, 58, 127])
    right_ear_center = get_region_center(points, [454, 323, 361, 288, 356])

    img = warp_region(img, left_eye_center, scale=eye_scale, radius=60)
    img = warp_region(img, right_eye_center, scale=eye_scale, radius=60)
    img = warp_region(img, face_outline_center, scale=nose_scale, radius=130)
    img = warp_region(img, left_ear_center, scale=ear_scale, radius=70)
    img = warp_region(img, right_ear_center, scale=ear_scale, radius=70)

    cv2.imwrite(output_path, img)
    print(f"✅ Exaggerated image saved to: {output_path}")
    return output_path

# ==========================
# GA Setup and Paths
# ==========================
real_path = "C:/Users/hp/OneDrive/Bureau/Bachelor Project/real_images/1.jpg"
gen_path = "C:/Users/hp/OneDrive/Bureau/Bachelor Project/Genetic/"
temp_cartoon = os.path.join(gen_path, "temp.jpg")
os.makedirs(gen_path, exist_ok=True)

def fitness_func(ga_instance, solution, solution_idx):
    saturation_boost, sharpness_factor, contrast_factor = solution
    cartoon_path = os.path.join(gen_path, f"gen_{solution_idx+1}.jpg")
    try:
        clean_and_soft_cartoonizer(real_path, cartoon_path, saturation_boost, sharpness_factor, contrast_factor)
        original = cv2.imread(real_path)
        cartoon = cv2.imread(cartoon_path)
        original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        cartoon_gray = cv2.cvtColor(cartoon, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(original_gray, cartoon_gray, full=True)
        return score
    except:
        return 0.0

ga = pygad.GA(
    num_generations=6,
    num_parents_mating=4,
    sol_per_pop=8,
    num_genes=3,
    init_range_low=0.6,
    init_range_high=2.0,
    mutation_percent_genes=10,
    fitness_func=fitness_func,
    gene_type=float
)
ga.run()

# ==========================
# Final Application
# ==========================
solution, _, _ = ga.best_solution()
print(f"\n🎯 Best GA Parameters:\n  Saturation={solution[0]:.2f}, Sharpness={solution[1]:.2f}, Contrast={solution[2]:.2f}")

final_cartoon_path = os.path.join(gen_path, "cartoon_output_final18.jpg")
exaggerated_path = os.path.join(gen_path, "cartoon_exaggerated_final18.jpg")
comparison_path = os.path.join(gen_path, "comparison18.jpg")

clean_and_soft_cartoonizer(real_path, final_cartoon_path, *solution)
exaggerate_features(final_cartoon_path, exaggerated_path)

# ==========================
# Display Comparison
# ==========================
original_img = Image.open(real_path).resize((300, 300))
output_img = Image.open(exaggerated_path).resize((300, 300))

fig, ax = plt.subplots(1, 2, figsize=(8, 4))
ax[0].imshow(original_img)
ax[0].set_title("Original")
ax[0].axis("off")
ax[1].imshow(output_img)
ax[1].set_title("Cartoonized + Exaggerated")
ax[1].axis("off")
plt.tight_layout()
plt.savefig(comparison_path)
plt.show()

# ==========================
# Show Fitness Curve
# ==========================
plt.figure(figsize=(8, 4))
plt.plot(ga.best_solutions_fitness, marker='o', color='blue')
plt.title("Best Fitness Value per Generation")
plt.xlabel("Generation")
plt.ylabel("SSIM Fitness Score")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(gen_path, "fitness_curve.png"))
plt.show()

# ==========================
# Log All Tried Solutions
# ==========================
print("\n🧬 Solutions Tried:")
for idx, sol in enumerate(ga.solutions):
    print(f"Gen {idx+1}: Saturation={sol[0]:.2f}, Sharpness={sol[1]:.2f}, Contrast={sol[2]:.2f}")
