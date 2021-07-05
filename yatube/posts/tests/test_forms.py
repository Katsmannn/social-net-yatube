import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            description='Описание тестовой группы',
            slug='test-group'
        )

        cls.post_1 = Post.objects.create(
            text='Содержимое тестового поста',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_create(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_im.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Содержимое добавленного тестового поста',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest('pub_date')
        self.assertEqual(new_post.group,
                         self.group)
        self.assertEqual(new_post.text,
                         'Содержимое добавленного тестового поста')
        self.assertEqual(new_post.image.name, 'posts/small_im.gif')

    def test_edit_post(self):
        post_text = self.post_1.text
        post_text_edit = post_text + ' (изменено)'
        form_data = {
            'text': post_text_edit,
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('post_edit', kwargs={'username': self.user.username,
                    'post_id': self.post_1.id}),
            data=form_data,
            follow=True
        )
        self.post_1.refresh_from_db()
        self.assertEqual(self.post_1.text, post_text_edit)
