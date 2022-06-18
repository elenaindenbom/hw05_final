import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
uploaded = SimpleUploadedFile(
    name='small.gif',
    content=small_gif,
    content_type='image/gif'
)

templates_post_pages_names = [
    reverse('posts:index'),
    reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
    reverse('posts:profile', kwargs={'username': 'SomeUser'}),
]


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = User.objects.create_user(username='Follower')
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.follower)
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='test-slug',
        )
        cls.wrong_group = Group.objects.create(
            title='Другая группа',
            slug='wrong_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Текст комментария',
            post=cls.post
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.user,
        )

    def tearDown(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        response = self.authorized_client.get('/')
        before_chenge = response.content
        test_post = Post.objects.create(
            author=self.user,
            text='Текст поста'
        )
        response = self.authorized_client.get('/')
        after_chenge = response.content
        self.assertEqual(before_chenge, after_chenge)
        cache.clear()
        response = self.authorized_client.get('/')
        after_chenge = response.content
        self.assertNotEqual(before_chenge, after_chenge)
        test_post.delete()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'SomeUser'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': '1'}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': '1'}): (
                'posts/create_post.html'
            ),
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_lists_pages_show_correct_context(self):
        """Шаблоны с постами сформированы с правильным контекстом."""
        for reverse_name in templates_post_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.id, self.post.id)
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.group, self.post.group)
                self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'})
        )
        object = response.context['post']
        self.assertEqual(object.id, self.post.id)
        self.assertEqual(object.image, self.post.image)

    def test_comment_exists_on_post_detail_page(self):
        """После успешной отправки комментарий появляется на странице поста"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '1'}))
        comment = response.context['comments']
        self.assertEqual(comment[0], self.comment)

    def test_follow(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        response = self.authorized_client_follower.get(reverse(
            'posts:follow_index'))
        post = response.context['page_obj']
        self.assertEqual(post[0], self.post)

    def test_follow_not(self):
        """Новая запись не пользователя появляется в ленте тех,
        кто на него не подписан"""
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        post = response.context['page_obj']
        self.assertNotIn(self.post, post)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        templates_pages_names = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
        ]
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }

                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)

    def test_group_post_on_wrong_group_page(self):
        """Пост, у которого указана группа, не появляется на страницах
        других групп"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'wrong_group'})
        )
        self.assertIsNotNone(response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Заголовок группы',
            slug='test-slug',
        )
        posts = []
        for i in range(13):
            posts.append(Post(
                author=cls.user,
                text='Текст поста',
                group=cls.group
            ))
        Post.objects.bulk_create(posts)

    def test_first_page_contains_ten_records(self):
        """Первая страница содержит десять постов"""
        for reverse_name in templates_post_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Вторая страница содержит три поста"""
        for reverse_name in templates_post_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
