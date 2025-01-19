from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from ...models import PreprocessedImage

class UploadImageViewTestCase(TestCase):

    def setUp(self):
        self.image_file = SimpleUploadedFile(
            "test_image.jpg",
            b"image_data",
            content_type="image/jpeg"
        )
        self.url = reverse('upload_image')

    @patch('apps.core.preprocessing.api.views.analyze_image_task')  # Corrected the patch target
    def test_upload_image_success(self, mock_analyze_image_task):

        self.image_file = SimpleUploadedFile("test_image.jpg", b"image_data")

        mock_analyze_image_task.return_value = None

        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        preprocessed_image = PreprocessedImage.objects.get(id=response.json()['preprocessed_image_id'])

        self.assertEqual(preprocessed_image.image.tobytes(), b"image_data")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"success": True, "message": "Image successfully uploaded and analysis started!",
             "preprocessed_image_id": preprocessed_image.id}
        )
        mock_analyze_image_task.assert_called_once_with(preprocessed_image.id)

    def test_upload_image_no_image(self):
        response = self.client.post(self.url, {}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error": "No image provided"}
        )

    @patch('apps.core.preprocessing.api.views.analyze_image_task')
    def test_upload_image_error(self, mock_analyze_image_task):

        mock_analyze_image_task.side_effect = Exception("Test error")

        response = self.client.post(self.url, {'image': self.image_file}, format='multipart')

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error": "Test error"}
        )
