from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            description='Описание тестовой группы',
            slug='test-group'
        )
        cls.post_1 = Post.objects.create(
            text='Содержимое тестового поста',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'index.html': '/',
            'newpost.html': '/new/',
            'group.html': f'/group/{self.group.slug}/',
            'profile.html': f'/{self.author.username}/',
            'post.html': f'/{self.author.username}/{self.post_1.id}/',
            'postedit.html': f'/{self.author.username}/{self.post_1.id}/edit/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                cache.clear()
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_profile_url_exists_at_desired_location(self):
        response = self.guest_client.get(f'/{self.author.username}/')
        self.assertEqual(response.status_code, 200)

    def test_post_url_exists_at_desired_location(self):
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post_1.id}/'
        )
        self.assertEqual(response.status_code, 200)

    def test_newpost_url_redirect_anonymous(self):
        response = self.guest_client.get('/new/')
        self.assertEqual(response.status_code, 302)

    def test_postedit_url_redirect_anonymous(self):
        response = self.guest_client.get(
            f'/{self.author.username}/{self.post_1.id}/edit/'
        )
        self.assertEqual(response.status_code, 302)

    def test_newpost_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_postedit_url_exists_at_desired_location(self):
        response = self.authorized_client.get(
            f'/{self.author.username}/{self.post_1.id}/edit/'
        )
        self.assertEqual(response.status_code, 200)

    def test_postedit_url_redirect_not_author(self):
        response = self.authorized_client_not_author.get(
            f'/{self.author.username}/{self.post_1.id}/edit/'
        )
        self.assertEqual(response.status_code, 302)

    def test_page_not_found_status(self):
        response = self.guest_client.get('/wrong_page/')
        self.assertEqual(response.status_code, 404)


class CommentURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='not_author')
        cls.post = Post.objects.create(
            text='Пост проверки комментирования',
            author=cls.author,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user)

    def test_add_comment_authorized_user(self):
        response = self.authorized_client_not_author.get(
            f'/{self.post.author.username}/{self.post.id}/comment'
        )
        self.assertEqual(response.status_code, 200)

    def test_add_comment_anonymous(self):
        response = self.guest_client.get(
            f'/{self.post.author.username}/{self.post.id}/comment'
        )
        self.assertEqual(response.status_code, 302)
