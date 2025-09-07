
import json
import base64
import io
from PIL import Image
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncImageResizer:
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size

    def resize_image(self, image_data, image_format='JPEG', quality=85):
        start_time = time.time()
        try:
            if isinstance(image_data, str):
                image_data = base64.b64decode(image_data)

            image = Image.open(io.BytesIO(image_data))
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')

            resized_image = image.resize(self.target_size, Image.Resampling.LANCZOS)

            output_buffer = io.BytesIO()
            resized_image.save(output_buffer, format=image_format, quality=quality)
            resized_data = output_buffer.getvalue()

            processing_time = time.time() - start_time

            return {
                'success': True,
                'resized_image': base64.b64encode(resized_data).decode('utf-8'),
                'original_size': len(image_data),
                'resized_size': len(resized_data),
                'compression_ratio': len(image_data) / len(resized_data),
                'processing_time': processing_time,
                'format': image_format
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        image_data = body.get('image')
        image_format = body.get('format', 'JPEG')
        quality = body.get('quality', 85)

        if not image_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No image data provided'})
            }

        resizer = AsyncImageResizer()
        result = resizer.resize_image(image_data, image_format, quality)

        if result['success']:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'resized_image': result['resized_image'],
                    'metadata': {
                        'original_size': result['original_size'],
                        'resized_size': result['resized_size'],
                        'compression_ratio': result['compression_ratio'],
                        'processing_time': result['processing_time'],
                        'format': result['format']
                    }
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': result['error']})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
