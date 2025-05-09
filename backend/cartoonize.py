# cartoonize.py
import torch
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
import mediapipe as mp
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
# Disable tkinter use completely
os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
import pygad

def clean_and_soft_cartoonizer(img_path, cartoon_path, saturation_boost=1.4, sharpness_factor=2.1, contrast_factor=1.5):
    """
    Cartoonize an image using a pre-trained model
    
    Parameters:
    -----------
    img_path : str
        Path to the input image
    cartoon_path : str
        Path to save the cartoonized image
    saturation_boost : float
        Factor to boost the saturation
    sharpness_factor : float
        Factor to enhance the sharpness
    contrast_factor : float
        Factor to enhance the contrast
    
    Returns:
    --------
    str
        Path to the saved cartoonized image
    """
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

def get_region_center(points, indices):
    """
    Calculate the center of a region defined by indices
    
    Parameters:
    -----------
    points : np.ndarray
        Array of points
    indices : list
        List of indices that define the region
    
    Returns:
    --------
    tuple
        Center coordinates (x, y)
    """
    coords = points[indices]
    center = np.mean(coords, axis=0).astype(int)
    return tuple(center)

def warp_region(img, center, scale=1.2, radius=30):
    """
    Warp a region of the image
    
    Parameters:
    -----------
    img : np.ndarray
        Input image
    center : tuple
        Center coordinates (x, y) of the region
    scale : float
        Scale factor for warping
    radius : int
        Radius of the region to warp
    
    Returns:
    --------
    np.ndarray
        Warped image
    """
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

def exaggerate_features(image_path, output_path, eye_scale=0.8, ear_scale=1.1, nose_scale=1.1):
    """
    Exaggerate facial features in an image
    
    Parameters:
    -----------
    image_path : str
        Path to the input image
    output_path : str
        Path to save the output image
    eye_scale : float
        Scale factor for eyes
    ear_scale : float
        Scale factor for ears
    nose_scale : float
        Scale factor for nose and face
    
    Returns:
    --------
    str
        Path to the saved output image
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")
        
    h, w = img.shape[:2]
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        # No face detected, just save the original image
        cv2.imwrite(output_path, img)
        return output_path

    landmarks = results.multi_face_landmarks[0]
    points = np.array([[int(p.x * w), int(p.y * h)] for p in landmarks.landmark])

    # Define regions for exaggeration
    left_eye_center = get_region_center(points, [33, 133, 159, 145, 160, 158])
    right_eye_center = get_region_center(points, [263, 362, 387, 373, 380, 385])
    nose_center = get_region_center(points, [152, 148, 377, 400, 378, 379])
    face_outline_center = get_region_center(points, list(range(0, 17)))
    left_ear_center = get_region_center(points, [234, 93, 132, 58, 127])
    right_ear_center = get_region_center(points, [454, 323, 361, 288, 356])

    # Apply warping to exaggerate features
    img = warp_region(img, left_eye_center, scale=eye_scale, radius=60)
    img = warp_region(img, right_eye_center, scale=eye_scale, radius=60)
    img = warp_region(img, face_outline_center, scale=nose_scale, radius=130)
    img = warp_region(img, left_ear_center, scale=ear_scale, radius=70)
    img = warp_region(img, right_ear_center, scale=ear_scale, radius=70)

    cv2.imwrite(output_path, img)
    return output_path

def optimize_cartoon_parameters(image_path, output_dir, num_generations=6, pop_size=8):
    """
    Use Genetic Algorithm to optimize cartoonization parameters
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_cartoon = os.path.join(output_dir, "temp.jpg")
    log_file = os.path.join(output_dir, "ga_log.txt")
    
    # Print a clear header for GA process in terminal
    print("\n" + "="*50)
    print(f"GENETIC ALGORITHM OPTIMIZATION STARTED")
    print(f"Image: {os.path.basename(image_path)}")
    print(f"Generations: {num_generations}, Population: {pop_size}")
    print("="*50)
    
    # Create log file
    with open(log_file, 'w') as f:
        f.write(f"GA Optimization Log\n")
        f.write(f"Image: {image_path}\n")
        f.write(f"Parameters: generations={num_generations}, population={pop_size}\n\n")

    def fitness_func(ga_instance, solution, solution_idx):
        saturation_boost, sharpness_factor, contrast_factor = solution
        cartoon_path = os.path.join(output_dir, f"gen_{solution_idx+1}.jpg")
        try:
            clean_and_soft_cartoonizer(image_path, cartoon_path, saturation_boost, sharpness_factor, contrast_factor)
            original = cv2.imread(image_path)
            cartoon = cv2.imread(cartoon_path)
            original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            cartoon_gray = cv2.cvtColor(cartoon, cv2.COLOR_BGR2GRAY)
            score, _ = ssim(original_gray, cartoon_gray, full=True)
            
            # Print solution evaluation to terminal with clear formatting
            print(f"Solution {solution_idx+1:02d}: sat={saturation_boost:.2f}, sharp={sharpness_factor:.2f}, " +
                  f"contrast={contrast_factor:.2f} → fitness={score:.4f}")
            
            # Log this solution
            with open(log_file, 'a') as f:
                f.write(f"Solution {solution_idx+1}: {solution} -> fitness={score:.4f}\n")
                
            return score
        except Exception as e:
            print(f"Error in fitness calculation: {e}")
            return 0.0

    # Create a callback function to log each generation
    def on_generation(ga_instance):
        generation = ga_instance.generations_completed
        best_solution = ga_instance.best_solution()
        best_fitness = best_solution[1]
        best_params = best_solution[0]
        
        # Print generation summary with visual separator
        print("\n" + "-"*50)
        print(f"GENERATION {generation}/{num_generations} COMPLETED")
        print(f"Best fitness: {best_fitness:.4f}")
        print(f"Best parameters: saturation={best_params[0]:.2f}, sharpness={best_params[1]:.2f}, " +
              f"contrast={best_params[2]:.2f}")
        print("-"*50)
        
        with open(log_file, 'a') as f:
            f.write(f"\nGeneration {generation} completed\n")
            f.write(f"Best fitness: {best_fitness:.4f}\n")
            f.write(f"Best parameters: {best_params}\n\n")
        
        # Save a plot of the fitness progress after each generation
        plot_ga_fitness(ga_instance, os.path.join(output_dir, f"fitness_gen_{generation}.png"))
        
        return False  # Don't stop the GA

    print(f"Creating GA with {num_generations} generations and population size {pop_size}")
    
    # Check pygad version and create GA instance accordingly
    try:
        # First, try the current implementation with callback_generation
        ga_kwargs = {
            "num_generations": num_generations,
            "num_parents_mating": 4,
            "sol_per_pop": pop_size,
            "num_genes": 3,
            "init_range_low": 0.6,
            "init_range_high": 2.0,
            "mutation_percent_genes": 10,
            "fitness_func": fitness_func,
            "gene_type": float,
            "callback_generation": on_generation,
            "stop_criteria": None
        }
        
        ga = pygad.GA(**ga_kwargs)
        print("Using GA with callback_generation")
    except TypeError as e:
        print("Older pygad version detected, using on_generation parameter instead")
        # For older versions of pygad
        ga_kwargs = {
            "num_generations": num_generations,
            "num_parents_mating": 4,
            "sol_per_pop": pop_size,
            "num_genes": 3,
            "init_range_low": 0.6,
            "init_range_high": 2.0,
            "mutation_percent_genes": 10,
            "fitness_func": fitness_func,
            "gene_type": float,
            "on_generation": on_generation,
        }
        
        ga = pygad.GA(**ga_kwargs)
    
    print("\nSTARTING GENETIC ALGORITHM RUN")
    print("Evaluating initial population...\n")
    ga.run()
    
    solution, fitness, solution_idx = ga.best_solution()
    
    # Print final results with clear visual formatting
    print("\n" + "="*50)
    print("GENETIC ALGORITHM OPTIMIZATION COMPLETED")
    print(f"Best fitness score: {fitness:.4f}")
    print(f"Optimal parameters:")
    print(f"  - Saturation:  {solution[0]:.2f}")
    print(f"  - Sharpness:   {solution[1]:.2f}")
    print(f"  - Contrast:    {solution[2]:.2f}")
    print("="*50 + "\n")
    
    # Save the final fitness curve
    plot_ga_fitness(ga, os.path.join(output_dir, "fitness_final.png"))
    
    # Save a summary to the log file
    with open(log_file, 'a') as f:
        f.write("\nOptimization Complete\n")
        f.write(f"Best fitness: {fitness:.4f}\n")
        f.write(f"Best parameters: saturation={solution[0]:.2f}, sharpness={solution[1]:.2f}, contrast={solution[2]:.2f}\n")
    
    return tuple(solution)

def create_comparison(original_path, cartoon_path, exaggerated_path, comparison_path):
    """
    Create a comparison image with original, cartoon and exaggerated versions
    
    Parameters:
    -----------
    original_path : str
        Path to the original image
    cartoon_path : str
        Path to the cartoon image
    exaggerated_path : str
        Path to the exaggerated image
    comparison_path : str
        Path to save the comparison image
    
    Returns:
    --------
    str
        Path to the saved comparison image
    """
    try:
        # Load images as PIL objects first to avoid tkinter issues
        original_img = Image.open(original_path).resize((300, 300))
        cartoon_img = Image.open(cartoon_path).resize((300, 300))
        exaggerated_img = Image.open(exaggerated_path).resize((300, 300))
        
        # Convert to numpy arrays for matplotlib (avoiding PIL-tkinter connection)
        original_arr = np.array(original_img)
        cartoon_arr = np.array(cartoon_img)
        exaggerated_arr = np.array(exaggerated_img)
        
        # Create the figure
        fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        ax[0].imshow(original_arr)
        ax[0].set_title("Original")
        ax[0].axis("off")
        
        ax[1].imshow(cartoon_arr)
        ax[1].set_title("Cartoonized")
        ax[1].axis("off")
        
        ax[2].imshow(exaggerated_arr)
        ax[2].set_title("Exaggerated")
        ax[2].axis("off")
        
        plt.tight_layout()
        plt.savefig(comparison_path)
        plt.close(fig)
        
        # Explicitly clean up resources
        del original_img, cartoon_img, exaggerated_img
        del original_arr, cartoon_arr, exaggerated_arr
        
        return comparison_path
    except Exception as e:
        print(f"Error creating comparison: {e}")
        # Provide a fallback - just copy the exaggerated image
        import shutil
        shutil.copy(exaggerated_path, comparison_path)
        return comparison_path

def plot_ga_fitness(ga_instance, output_path):
    """
    Plot the fitness curve from GA optimization
    
    Parameters:
    -----------
    ga_instance : pygad.GA
        GA instance that has been run
    output_path : str
        Path to save the fitness curve plot
    
    Returns:
    --------
    str
        Path to the saved fitness curve plot
    """
    try:
        plt.figure(figsize=(8, 4))
        plt.plot(ga_instance.best_solutions_fitness, marker='o', color='blue')
        plt.title("Best Fitness Value per Generation")
        plt.xlabel("Generation")
        plt.ylabel("SSIM Fitness Score")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path
    except Exception as e:
        print(f"Error plotting fitness: {e}")
        return None