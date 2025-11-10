"""
Client for communicating with the FastAPI face recognition service
"""
import requests
import json
from django.conf import settings


class FaceAPIClient:
    """Client to interact with FastAPI face service backend"""
    
    def __init__(self):
        # You'll configure this URL in settings.py
        self.base_url = getattr(settings, 'FACE_API_URL', 'http://localhost:8000')
    
    def enroll_student(self, student_id, student_name, class_code, image_files):
        """
        Send student enrollment data to FastAPI for face feature extraction
        
        Args:
            student_id: Unique student identifier
            student_name: Student's full name
            class_code: Unique class enrollment code
            image_files: List of image file objects (3 images)
        
        Returns:
            dict: Response from FastAPI with face encoding data
        """
        url = f"{self.base_url}/api/enroll"
        
        # FastAPI expects separate file fields: image1, image2, image3
        files = {
            'image1': (f'image1.jpg', image_files[0], 'image/jpeg'),
            'image2': (f'image2.jpg', image_files[1], 'image/jpeg'),
            'image3': (f'image3.jpg', image_files[2], 'image/jpeg')
        }
        
        data = {
            'student_id': student_id,
            'student_name': student_name,
            'class_code': class_code
        }
        
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def mark_attendance(self, class_code, image_files):
        """
        Send class photos to FastAPI for attendance marking via facial recognition
        
        Args:
            class_code: Unique class enrollment code
            image_files: List of 3 image file objects from the classroom
        
        Returns:
            dict: Response with list of recognized students
        """
        url = f"{self.base_url}/api/mark-attendance"
        
        # FastAPI expects separate file fields: classroom_image1, classroom_image2, classroom_image3
        files = {
            'classroom_image1': (f'classroom1.jpg', image_files[0], 'image/jpeg'),
            'classroom_image2': (f'classroom2.jpg', image_files[1], 'image/jpeg'),
            'classroom_image3': (f'classroom3.jpg', image_files[2], 'image/jpeg')
        }
        
        data = {
            'class_code': class_code
        }
        
        try:
            response = requests.post(url, files=files, data=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'present_students': result.get('present_students', []),
                'total_detected': result.get('total_detected', 0),
                'confidence_scores': result.get('confidence_scores', {})
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_student_encodings(self, class_code):
        """
        Retrieve all face encodings for students in a specific class
        
        Args:
            class_code: Unique class enrollment code
        
        Returns:
            dict: Student encodings data
        """
        url = f"{self.base_url}/api/encodings/{class_code}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_enrollment_session(self, user_id):
        """
        Start a pose-based enrollment session
        
        Args:
            user_id: Unique user identifier
        
        Returns:
            dict: Session info with required poses
        """
        url = f"{self.base_url}/enroll/start"
        
        try:
            response = requests.post(url, json={'user_id': user_id}, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_enrollment_frame(self, user_id, image_file):
        """
        Process a single frame for pose-based enrollment
        
        Args:
            user_id: Unique user identifier
            image_file: Image file object (frame from webcam)
        
        Returns:
            dict: Feedback with pose guidance and capture status
        """
        url = f"{self.base_url}/enroll/process-frame/{user_id}"
        
        try:
            files = {'file': image_file}
            response = requests.post(url, files=files, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def complete_enrollment(self, user_id):
        """
        Complete pose-based enrollment and save to database
        
        Args:
            user_id: Unique user identifier
        
        Returns:
            dict: Completion status
        """
        url = f"{self.base_url}/enroll/complete/{user_id}"
        
        try:
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_enrollment(self, user_id):
        """
        Cancel an enrollment session
        
        Args:
            user_id: Unique user identifier
        
        Returns:
            dict: Cancellation status
        """
        url = f"{self.base_url}/enroll/cancel/{user_id}"
        
        try:
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
