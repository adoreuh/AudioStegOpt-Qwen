import os
import sys
import uuid
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
import traceback
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.final_system import FinalStegoSystem
from core.improved_stego import CapacityExceededError, ExtractionError
from utils.qwen_integration import QwenModelIntegration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False

CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

stego_system = FinalStegoSystem(use_mamba=True, use_ai=True)
qwen_model = QwenModelIntegration()

HISTORY_FILE = os.path.join(BASE_DIR, 'operation_history.json')

ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg'}
ALLOWED_MIME_TYPES = {'audio/wav', 'audio/mpeg', 'audio/flac', 'audio/ogg', 'audio/x-wav'}
FILE_SIGNATURES = {
    b'ID3': 'mp3',
    b'\xff\xfb': 'mp3',
    b'\xff\xfa': 'mp3',
    b'RIFF': 'wav',
    b'fLaC': 'flac',
    b'OggS': 'ogg'
}

def validate_file(file_storage):
    if not file_storage:
        return False, "No file provided"
    
    filename = file_storage.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    file_storage.seek(0)
    header = file_storage.read(10)
    file_storage.seek(0)
    
    if len(header) < 4:
        return False, "File too small or corrupted"
    
    detected_type = None
    for sig, ftype in FILE_SIGNATURES.items():
        if header[:len(sig)] == sig:
            detected_type = ftype
            break
    
    if detected_type is None and ext == '.mp3':
        detected_type = 'mp3'
    
    if detected_type is None:
        return False, "Unable to detect file type"
    
    return True, detected_type

def safe_filename(filename):
    filename = os.path.basename(filename)
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    return filename

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/embed', methods=['POST'])
def embed_message():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '请上传音频文件'}), 400
        
        audio_file = request.files['audio']
        message = request.form.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': '请输入要嵌入的消息'}), 400
        
        if len(message.encode('utf-8')) > 100000:
            return jsonify({'success': False, 'error': '消息过长，最大支持100KB'}), 400
        
        is_valid, file_info = validate_file(audio_file)
        if not is_valid:
            return jsonify({'success': False, 'error': file_info}), 400
        
        file_ext = os.path.splitext(audio_file.filename)[1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{file_ext}")
        audio_file.save(input_path)
        
        output_filename = f"stego_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        try:
            result = stego_system.embed_message(input_path, message, output_path)
        except CapacityExceededError as e:
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 400
        except ValueError as e:
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 400
        
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")
        
        if result['success']:
            history = load_history()
            history.append({
                'id': uuid.uuid4().hex,
                'operation': 'embed',
                'filename': safe_filename(audio_file.filename),
                'output_filename': output_filename,
                'message_length': len(message),
                'timestamp': datetime.now().isoformat(),
                'snr': result['metrics']['snr'],
                'psnr': result['metrics']['psnr']
            })
            save_history(history)
            
            return jsonify({
                'success': True,
                'output_file': output_filename,
                'download_url': f'/api/download/{output_filename}',
                'metrics': result['metrics']
            })
        else:
            error_msg = result.get('error', '嵌入失败')
            logger.error(f"Embed failed: {error_msg}")
            return jsonify({'success': False, 'error': '处理失败，请重试'}), 500
            
    except Exception as e:
        logger.error(f"Embed error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/extract', methods=['POST'])
def extract_message():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '请上传音频文件'}), 400
        
        audio_file = request.files['audio']
        embedding_info_str = request.form.get('embedding_info', None)
        
        is_valid, file_info = validate_file(audio_file)
        if not is_valid:
            return jsonify({'success': False, 'error': file_info}), 400
        
        file_ext = os.path.splitext(audio_file.filename)[1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{file_ext}")
        audio_file.save(input_path)
        
        embedding_info = None
        if embedding_info_str:
            try:
                embedding_info = json.loads(embedding_info_str)
            except json.JSONDecodeError:
                if os.path.exists(input_path):
                    try:
                        os.remove(input_path)
                    except Exception:
                        pass
                return jsonify({'success': False, 'error': 'embedding_info格式错误'}), 400
        
        if embedding_info is None:
            capacity = stego_system.get_capacity(input_path)
            if capacity['success']:
                embedding_info = {
                    'data_length': min(capacity['capacity']['total'], 1000)
                }
        
        try:
            result = stego_system.extract_message(input_path, embedding_info)
        except ExtractionError as e:
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 400
        except ValueError as e:
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except Exception:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 400
        
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")
        
        if result['success']:
            history = load_history()
            history.append({
                'id': uuid.uuid4().hex,
                'operation': 'extract',
                'filename': safe_filename(audio_file.filename),
                'message_length': len(result['extracted_message']),
                'timestamp': datetime.now().isoformat()
            })
            save_history(history)
            
            return jsonify({
                'success': True,
                'message': result['extracted_message'],
                'extraction_info': result.get('extraction_info', {})
            })
        else:
            error_msg = result.get('error', '提取失败')
            logger.error(f"Extract failed: {error_msg}")
            return jsonify({'success': False, 'error': '提取失败，请确认文件包含隐藏信息'}), 500
            
    except Exception as e:
        logger.error(f"Extract error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/capacity', methods=['POST'])
def get_capacity():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '请上传音频文件'}), 400
        
        audio_file = request.files['audio']
        
        is_valid, file_info = validate_file(audio_file)
        if not is_valid:
            return jsonify({'success': False, 'error': file_info}), 400
        
        file_ext = os.path.splitext(audio_file.filename)[1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{file_ext}")
        audio_file.save(input_path)
        
        result = stego_system.get_capacity(input_path)
        
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Capacity error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/audio-info', methods=['POST'])
def get_audio_info():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '请上传音频文件'}), 400
        
        audio_file = request.files['audio']
        
        is_valid, file_info = validate_file(audio_file)
        if not is_valid:
            return jsonify({'success': False, 'error': file_info}), 400
        
        file_ext = os.path.splitext(audio_file.filename)[1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{file_ext}")
        audio_file.save(input_path)
        
        try:
            audio_data, sample_rate = stego_system.audio_processor.load_audio(input_path)
            
            duration = len(audio_data) / sample_rate
            audio_info = {
                'duration': duration,
                'sample_rate': sample_rate,
                'length': len(audio_data),
                'channels': 1,
                'max_amplitude': float(np.max(np.abs(audio_data))),
                'rms': float(np.sqrt(np.mean(audio_data ** 2)))
            }
            
            result = {
                'success': True,
                'info': audio_info
            }
        except Exception as e:
            result = {'success': False, 'error': str(e)}
        
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Audio info error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    try:
        safe_name = safe_filename(filename)
        
        if not safe_name or safe_name != filename:
            return jsonify({'success': False, 'error': '无效的文件名'}), 400
        
        if not safe_name.startswith('stego_') or not safe_name.endswith('.wav'):
            return jsonify({'success': False, 'error': '无效的文件名'}), 400
        
        file_path = os.path.join(OUTPUT_DIR, safe_name)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在或已过期'}), 404
        
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=safe_name,
            mimetype='audio/wav'
        )
        
    except Exception as e:
        logger.error(f"Download error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': '下载失败'}), 500

@app.route('/api/outputs/<filename>')
def serve_output(filename):
    try:
        safe_name = safe_filename(filename)
        return send_from_directory(OUTPUT_DIR, safe_name)
    except Exception as e:
        return jsonify({'success': False, 'error': '文件不存在'}), 404

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        history = load_history()
        limit = request.args.get('limit', 20, type=int)
        return jsonify({
            'success': True,
            'history': history[-limit:]
        })
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'success': False, 'error': '获取历史失败'}), 500

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    try:
        save_history([])
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({'success': False, 'error': '清空失败'}), 500

@app.route('/api/ai/optimize', methods=['POST'])
def ai_optimize():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '请上传音频文件'}), 400
        
        audio_file = request.files['audio']
        message = request.form.get('message', '')
        
        if not qwen_model.check_model_availability():
            return jsonify({'success': False, 'error': 'AI模型不可用'}), 503
        
        is_valid, file_info = validate_file(audio_file)
        if not is_valid:
            return jsonify({'success': False, 'error': file_info}), 400
        
        file_ext = os.path.splitext(audio_file.filename)[1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{file_ext}")
        audio_file.save(input_path)
        
        audio_info = stego_system.analyze_audio(input_path)
        
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception:
                pass
        
        if not audio_info['success']:
            return jsonify({'success': False, 'error': '音频分析失败'}), 400
        
        optimization = qwen_model.optimize_embedding_parameters(
            audio_info['analysis'].get('basic', {}), len(message)
        )
        
        return jsonify({
            'success': True,
            'optimization': optimization
        })
        
    except Exception as e:
        logger.error(f"AI optimize error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': 'AI优化失败'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'ai_model_available': qwen_model.check_model_availability(),
        'output_dir': OUTPUT_DIR,
        'output_dir_exists': os.path.exists(OUTPUT_DIR)
    })

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': '文件过大，最大支持50MB'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, app, use_debugger=debug_mode, use_reloader=False)