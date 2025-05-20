# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import tempfile
import time
from werkzeug.utils import secure_filename

# Import your cartoonizer functions
from cartoonize import (
    clean_and_soft_cartoonizer, 
    exaggerate_features, 
    optimize_cartoon_parameters,
    create_comparison,
    plot_ga_fitness,
    fast_exaggerate_features  # Add this import
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

TEMP_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/cartoonize', methods=['POST'])
def cartoonize_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Get parameters from the request
            optimize = request.form.get('optimize', 'false').lower() == 'true'
            caricature_mode = request.form.get('caricature', 'false').lower() == 'true'
            
            # Get slider values directly from the request
            saturation_boost = float(request.form.get('saturation', 1.4))
            sharpness_factor = float(request.form.get('sharpness', 2.1))
            contrast_factor = float(request.form.get('contrast', 1.5))
            
            # Always get eye_scale and nose_scale from request parameters
            # This allows the real-time slider adjustments to work
            eye_scale = float(request.form.get('eye_scale', 0.8 if not caricature_mode else 0.35))
            ear_scale = 1.1  # Keep default ear scale
            nose_scale = float(request.form.get('nose_scale', 1.1 if not caricature_mode else 0.45))
            
            # Validate eye_scale and nose_scale to prevent extreme values that could break the image
            eye_scale = max(0.1, min(eye_scale, 2.0))    # Ensure within reasonable range
            nose_scale = max(0.1, min(nose_scale, 2.0))  # Ensure within reasonable range
            
            print(f"Received request to cartoonize image: {file.filename}")
            print(f"Parameters: optimize={optimize}, caricature={caricature_mode}")
            print(f"Eye scale: {eye_scale}, Nose scale: {nose_scale}")
            
            # Create session folder with timestamp to separate different uploads
            session_id = str(int(time.time()))
            session_folder = os.path.join(TEMP_FOLDER, f"cartoonizer_{session_id}")
            os.makedirs(session_folder, exist_ok=True)
            
            # Create temporary files for processing
            input_filename = secure_filename(file.filename)
            input_path = os.path.join(session_folder, input_filename)
            cartoon_path = os.path.join(session_folder, "cartoon_" + input_filename)
            exaggerated_path = os.path.join(session_folder, "exaggerated_" + input_filename)
            comparison_path = os.path.join(session_folder, "comparison_" + input_filename)
            
            print(f"Saving input file to: {input_path}")
            
            # Save the uploaded file
            file.save(input_path)
            
            if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
                return jsonify({'error': 'Failed to save uploaded file'}), 500
                
            print(f"File saved successfully, size: {os.path.getsize(input_path)} bytes")
            
            # If optimization is requested, use GA to optimize parameters
            if optimize:
                print(f"\n{'*'*70}")
                print(f"* STARTING GA OPTIMIZATION FOR: {input_filename}")
                print(f"* Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"* Session ID: {session_id}")
                print(f"{'*'*70}")
                
                # Create a subdirectory for GA optimization files
                ga_folder = os.path.join(session_folder, "ga_optimization")
                os.makedirs(ga_folder, exist_ok=True)
                
                # Run GA optimization
                start_time = time.time()
                saturation_boost, sharpness_factor, contrast_factor = optimize_cartoon_parameters(
                    input_path, 
                    ga_folder,
                    num_generations=4,  # Reduced for faster response
                    pop_size=6
                )
                end_time = time.time()
                
                print(f"{'*'*70}")
                print(f"* GA OPTIMIZATION COMPLETED")
                print(f"* Time taken: {end_time - start_time:.2f} seconds")
                print(f"* Optimized parameters:")
                print(f"*   - Saturation: {saturation_boost:.2f}")
                print(f"*   - Sharpness:  {sharpness_factor:.2f}")
                print(f"*   - Contrast:   {contrast_factor:.2f}")
                print(f"{'*'*70}\n")
                
                # Also create a summary file in the session folder
                with open(os.path.join(session_folder, "optimization_summary.txt"), "w") as f:
                    f.write(f"Optimization Summary\n")
                    f.write(f"===================\n\n")
                    f.write(f"Image: {input_filename}\n")
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Processing time: {end_time - start_time:.2f} seconds\n\n")
                    f.write(f"Optimized Parameters:\n")
                    f.write(f"  Saturation: {saturation_boost:.2f}\n")
                    f.write(f"  Sharpness: {sharpness_factor:.2f}\n")
                    f.write(f"  Contrast: {contrast_factor:.2f}\n")
            
            # Process the image using your functions with the provided parameters
            print(f"Applying cartoonization with parameters: saturation={saturation_boost}, sharpness={sharpness_factor}, contrast={contrast_factor}")
            clean_and_soft_cartoonizer(
                input_path, 
                cartoon_path, 
                saturation_boost=saturation_boost, 
                sharpness_factor=sharpness_factor, 
                contrast_factor=contrast_factor
            )
            
            if not os.path.exists(cartoon_path):
                return jsonify({'error': 'Cartoonization failed to produce output image'}), 500
                
            print(f"Cartoonization complete, applying feature exaggeration")
            print(f"Using scales: eye_scale={eye_scale}, ear_scale={ear_scale}, nose_scale={nose_scale}")
            
            # Apply feature exaggeration - using the slider values
            exaggerate_features(
                cartoon_path, 
                exaggerated_path, 
                eye_scale=eye_scale, 
                ear_scale=ear_scale, 
                nose_scale=nose_scale
            )
            
            if not os.path.exists(exaggerated_path):
                return jsonify({'error': 'Feature exaggeration failed to produce output image'}), 500
                
            print(f"Feature exaggeration complete, creating comparison image")
            
            # Create comparison image
            create_comparison(input_path, cartoon_path, exaggerated_path, comparison_path)
            
            # Convert the output images to base64 for sending back to the client
            result_images = {}
            
            try:
                for img_type, img_path in [
                    ('cartoon', cartoon_path), 
                    ('exaggerated', exaggerated_path),
                    ('comparison', comparison_path)
                ]:
                    if os.path.exists(img_path):
                        with open(img_path, "rb") as image_file:
                            # Get the file extension (without the dot)
                            file_ext = os.path.splitext(img_path)[1][1:]
                            # Map file extension to MIME type
                            mime_type = 'jpeg' if file_ext.lower() == 'jpg' else file_ext.lower()
                            # Create the data URL with proper MIME type
                            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                            result_images[img_type] = f"data:image/{mime_type};base64,{base64_image}"
                            
                            # Print debug information
                            print(f"Base64 {img_type} length: {len(base64_image)}")
                    else:
                        print(f"Warning: {img_path} does not exist")
            except Exception as e:
                print(f"Error encoding images: {str(e)}")
                return jsonify({'error': f'Error encoding images: {str(e)}'}), 500
            
            # Add parameters to the response
            parameters = {
                'saturation': saturation_boost,
                'sharpness': sharpness_factor,
                'contrast': contrast_factor,
                'eye_scale': eye_scale,
                'ear_scale': ear_scale,
                'nose_scale': nose_scale,
                'optimized': optimize,
                'caricature': caricature_mode
            }
            
            print("Successfully processed image, returning response")
            return jsonify({
                'success': True,
                'images': result_images,
                'parameters': parameters
            })
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"Error processing image: {str(e)}")
            print(tb)
            return jsonify({'error': str(e), 'traceback': tb}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/status', methods=['GET'])
def server_status():
    """Check if the server is running correctly"""
    return jsonify({
        'status': 'ok',
        'message': 'Cartoonizer server is running',
        'version': '1.0.0'
    })

@app.route('/adjust-features', methods=['POST'])
def adjust_features():
    """Lightweight endpoint for slider adjustments"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Get all slider values from the request
            eye_scale = float(request.form.get('eye_scale', 0.8))
            nose_scale = float(request.form.get('nose_scale', 1.1))
            saturation_boost = float(request.form.get('saturation', 1.4))
            contrast_factor = float(request.form.get('contrast', 1.5))
            sharpness_factor = float(request.form.get('sharpness', 2.1))
            caricature_mode = request.form.get('caricature', 'false').lower() == 'true'
            
            # Enforce limits to prevent extreme values
            eye_scale = max(0.1, min(eye_scale, 2.0))
            nose_scale = max(0.1, min(nose_scale, 2.0))
            saturation_boost = max(0.5, min(saturation_boost, 2.5))
            contrast_factor = max(0.5, min(contrast_factor, 3.0))
            sharpness_factor = max(0.5, min(sharpness_factor, 3.0))
            
            # Log the received parameters
            print(f"Adjusting image: eye={eye_scale}, nose={nose_scale}, "
                  f"sat={saturation_boost}, contrast={contrast_factor}, sharp={sharpness_factor}")
            
            # Create temporary folder for processing
            session_id = str(int(time.time()))
            session_folder = os.path.join(TEMP_FOLDER, f"adjust_{session_id}")
            os.makedirs(session_folder, exist_ok=True)
            
            # Create file paths
            input_filename = secure_filename(file.filename)
            input_path = os.path.join(session_folder, input_filename)
            cartoon_path = os.path.join(session_folder, "cartoon_" + input_filename)
            adjusted_path = os.path.join(session_folder, "adjusted_" + input_filename)
            
            # Save uploaded file
            file.save(input_path)
            
            # Apply cartoonization with the requested parameters
            clean_and_soft_cartoonizer(
                input_path, 
                cartoon_path, 
                saturation_boost=saturation_boost,
                sharpness_factor=sharpness_factor, 
                contrast_factor=contrast_factor
            )
            
            # Apply feature exaggeration
            fast_exaggerate_features(
                cartoon_path,
                adjusted_path,
                eye_scale=eye_scale,
                ear_scale=1.1,  # Keep ear scale constant
                nose_scale=nose_scale
            )
            
            # Convert result to base64
            with open(adjusted_path, "rb") as image_file:
                file_ext = os.path.splitext(adjusted_path)[1][1:]
                mime_type = 'jpeg' if file_ext.lower() == 'jpg' else file_ext.lower()
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                result_image = f"data:image/{mime_type};base64,{base64_image}"
            
            return jsonify({
                'success': True,
                'image': result_image,
                'parameters': {
                    'eye_scale': eye_scale,
                    'nose_scale': nose_scale,
                    'saturation': saturation_boost,
                    'contrast': contrast_factor,
                    'sharpness': sharpness_factor
                }
            })
            
        except Exception as e:
            import traceback
            print(f"Error during adjustment: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)