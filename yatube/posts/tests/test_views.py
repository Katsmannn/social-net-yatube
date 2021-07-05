import datetime as dt

import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            description='Описание тестовой группы',
            slug='test-group'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_context.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post_1 = Post.objects.create(
            text='Содержимое тестового поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        templates_pages_names = {
            'index.html': reverse('index'),
            'newpost.html': reverse('new_post'),
            'group.html': (
                reverse('group_detail', kwargs={'slug': self.group.slug})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        post = response.context['page'][0]
        text = post.text
        author = post.author
        pub_date = post.pub_date
        group = post.group
        image = post.image
        self.assertEqual(text, self.post_1.text)
        self.assertEqual(author.username, self.post_1.author.username)
        self.assertEqual(pub_date.date(), dt.datetime.now().date())
        self.assertEqual(group.title, self.post_1.group.title)
        self.assertEqual(image.name, self.post_1.image.name)

    def test_group_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'group_detail',
                kwargs={'slug': self.group.slug}
            )
        )
        post_context = response.context['page'][0]
        self.assertEqual(response.context['group'].title,
                         self.post_1.group.title)
        self.assertEqual(response.context['group'].description,
                         self.post_1.group.description)
        self.assertEqual(response.context['group'].slug,
                         self.post_1.group.slug)
        self.assertEqual(post_context.image.name, self.post_1.image.name)
        self.assertIsInstance(post_context, Post)

    def test_newpost_correct_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_postedit_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'post_edit',
                kwargs={'username': self.post_1.author.username,
                        'post_id': self.post_1.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(
            reverse('profile', args=[self.post_1.author.username])
        )
        post = response.context['page'][0]
        text = post.text
        author = post.author
        pub_date = post.pub_date
        group = post.group
        image = post.image
        self.assertEqual(text, self.post_1.text)
        self.assertEqual(author.username, self.post_1.author.username)
        self.assertEqual(pub_date.date(), dt.datetime.now().date())
        self.assertEqual(group.title, self.post_1.group.title)
        self.assertEqual(response.context['author'].username,
                         self.post_1.author.username)
        self.assertEqual(image.name, self.post_1.image.name)
        self.assertEqual(response.context['count'], 1)

    def test_post_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'post',
                kwargs={'username': self.post_1.author.username,
                        'post_id': self.post_1.id}
            )
        )
        post = response.context['post']
        text = post.text
        author = post.author
        pub_date = post.pub_date
        group = post.group
        image = post.image
        self.assertEqual(text, self.post_1.text)
        self.assertEqual(author.username, self.post_1.author.username)
        self.assertEqual(pub_date.date(), dt.datetime.now().date())
        self.assertEqual(group.title, self.post_1.group.title)
        self.assertEqual(response.context['author'].username,
                         self.post_1.author.username)
        self.assertEqual(image.name, self.post_1.image.name)
        self.assertEqual(response.context['count'], 1)

    def test_post_with_group_on_wrong_group_page_context(self):
        self.group_1 = Group.objects.create(
            title='Заголовок тестовой группы1',
            description='Описание тестовой группы1',
            slug='test-group1'
        )
        result_pages_names = {
            reverse('index'): 1,
            reverse('group_detail', kwargs={'slug': self.group.slug}): 1,
            reverse('group_detail', kwargs={'slug': self.group_1.slug}): 0,
        }
        for reverse_name, result in result_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page'].object_list),
                                 result)

    def test_index_cache_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page'].object_list),
                         Post.objects.all().count())
        Post.objects.create(
            text='Проверка cache',
            author=self.user,
        )
        response = self.authorized_client.get(reverse('index'))
        self.assertIsNone(response.context)
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        post = response.context['page'][0]
        text = post.text
        self.assertEqual(text, 'Проверка cache')
        Post.objects.latest('pub_date').delete()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            description='Описание тестовой группы',
            slug='test-group'
        )
        for i in range(13):
            Post.objects.create(
                text=f'Содержимое тестового поста {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        pages_names = [
            reverse('index'),
            reverse('profile', args=[self.user.username]),
            reverse('group_detail', kwargs={'slug': self.group.slug}),
        ]
        for reverse_name in pages_names:
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context.get('page').object_list),
                                 10)

    def test_second_page_contains_three_records(self):
        cache.clear()
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower_user = User.objects.create_user(
            username='follower_user'
        )
        cls.following_user = User.objects.create_user(
            username='following_user'
        )
        cls.not_follower_user = User.objects.create_user(
            username='not_follower_user'
        )
        cls.post_follow = Post.objects.create(
            text='Пост для проверки подписок',
            author=cls.following_user,
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower_user)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower_user)

    def test_follow_and_unfollow(self):
        follow_count = Follow.objects.all().count()
        self.follower_client.get(
            reverse('profile_follow', args=[self.following_user.username])
        )
        self.assertEqual(Follow.objects.all().count(), follow_count + 1)
        self.follower_client.get(
            reverse('profile_unfollow', args=[self.following_user.username])
        )
        self.assertEqual(Follow.objects.all().count(), follow_count)

    def test_follow_index(self):
        self.follower_client.get(
            reverse('profile_follow', args=[self.following_user.username])
        )
        response_follow = self.follower_client.get(reverse('follow_index'))
        post = response_follow.context['page'][0]
        self.assertEqual(post.text, self.post_follow.text)
        response_not_follow = self.not_follower_client.get(
            reverse('follow_index')
        )
        post = response_not_follow.context['page'].object_list.count()
        self.assertEqual(post, 0)


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            text='Пост для проверки комментирования',
            author=cls.authorized_user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_add_comment_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.post.author.username,
                    'post_id': self.post.id
                }
            )
        )
        self.assertIsInstance(response.context['form'].fields['text'],
                              forms.fields.CharField)
