"""
Simple mock face recognition service for development/testing purposes.
This is a placeholder implementation that allows the application to run
without the complex face_recognition library dependencies.
"""
import json
import base64
from io import BytesIO
import os
from typing import List, Dict, Any, Optional


class SimpleFaceRecognitionService:
    def __init__(self):
        self.known_faces = []  # List of dictionaries containing face encodings and metadata
        self.known_face_names = []  # List of names
        self.known_face_ids = []  # List of student IDs
    
    def add_known_face(self, face_encoding, name: str, student_id: int):
        """Add a known face to the recognition system."""
        self.known_faces.append({
            'encoding': face_encoding,
            'name': name,
            'id': student_id
        })
        self.known_face_names.append(name)
        self.known_face_ids.append(student_id)
    
    def clear_known_faces(self):
        """Clear all known faces from the system."""
        self.known_faces = []
        self.known_face_names = []
        self.known_face_ids = []
    
    def get_known_faces_count(self) -> int:
        """Get the number of known faces."""
        return len(self.known_faces)
    
    def load_face_from_image_path(self, image_path: str):
        """
        Load face encoding from an image file.
        Returns a mock face encoding (list of 128 floats) for development.
        """
        if not os.path.exists(image_path):
            return None
        
        try:
            # Mock face encoding - just return a list of 128 random-ish numbers
            # In a real implementation, this would use face_recognition.face_encodings()
            import hashlib
            
            # Create a deterministic "encoding" based on the image path
            hash_obj = hashlib.md5(image_path.encode())
            hex_hash = hash_obj.hexdigest()
            
            # Convert hash to a list of 128 floats between -1 and 1
            encoding = []
            for i in range(0, 128):
                # Use different parts of the hash to generate numbers
                hex_part = hex_hash[(i % 32)] + hex_hash[((i + 1) % 32)]
                num = int(hex_part, 16) / 255.0  # Convert to 0-1
                num = (num - 0.5) * 2  # Convert to -1 to 1
                encoding.append(num)
            
            return encoding
        except Exception as e:
            print(f"Error loading face from {image_path}: {str(e)}")
            return None
    
    def get_face_encoding_as_json(self, face_encoding) -> str:
        """Convert face encoding to JSON string for storage."""
        if face_encoding is None:
            return None
        return json.dumps(face_encoding)
    
    def load_face_encoding_from_json(self, json_str: str):
        """Load face encoding from JSON string."""
        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except Exception as e:
            print(f"Error loading face encoding from JSON: {str(e)}")
            return None
    
    def recognize_faces_in_image(self, image_data, tolerance: float = 0.6) -> List[Dict[str, Any]]:
        """
        Recognize faces in an image.
        
        Args:
            image_data: Can be image bytes or base64 encoded string
            tolerance: Recognition tolerance (lower = more strict)
        
        Returns:
            List of recognition results with id, name, and confidence
        """
        try:
            # For development purposes, return mock results
            # In a real implementation, this would:
            # 1. Load the image from bytes/base64
            # 2. Find all face locations and encodings
            # 3. Compare against known faces
            # 4. Return matches with confidence scores
            
            results = []
            
            # Mock: Simulate finding 1-3 faces with varying confidence
            # For development, we'll return some mock data
            if len(self.known_faces) > 0:
                # Simulate recognizing the first known face with high confidence
                face = self.known_faces[0]
                results.append({
                    'id': face['id'],
                    'name': face['name'],
                    'confidence': 85.0,  # Mock high confidence
                    'location': {'top': 100, 'right': 200, 'bottom': 300, 'left': 50}  # Mock face location
                })
            
            # Sometimes add an unrecognized face
            if len(results) == 0 or (len(self.known_faces) > 1 and len(results) < 2):
                results.append({
                    'id': None,
                    'name': 'Unknown',
                    'confidence': 45.0,  # Mock low confidence
                    'location': {'top': 150, 'right': 250, 'bottom': 350, 'left': 100}
                })
            
            return results
            
        except Exception as e:
            print(f"Error in face recognition: {str(e)}")
            return []
    
    def _decode_base64_image(self, base64_string: str) -> bytes:
        """Helper method to decode base64 image string to bytes."""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',', 1)[1]
            
            return base64.b64decode(base64_string)
        except Exception as e:
            print(f"Error decoding base64 image: {str(e)}")
            raise