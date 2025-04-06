from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Comment

User = get_user_model()

class CommentTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')
        
        # Create a test post
        self.post = Post.objects.create(
            user=self.user1,
            content="Test post for comments"
        )
        
        # Login as user1
        self.client = Client()
        self.client.login(username='testuser1', password='testpassword1')
    
    def test_nested_comments(self):
        """Test that nested comments can go beyond two levels deep"""
        # Create top-level comment
        top_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content="Top level comment"
        )
        
        # Create first level reply
        level1_reply = Comment.objects.create(
            user=self.user2,
            post=self.post,
            content="Level 1 reply",
            parent=top_comment
        )
        
        # Create second level reply
        level2_reply = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content="Level 2 reply",
            parent=level1_reply
        )
        
        # Create third level reply
        level3_reply = Comment.objects.create(
            user=self.user2,
            post=self.post,
            content="Level 3 reply",
            parent=level2_reply
        )
        
        # Get comments API response
        response = self.client.get(reverse('get_comments', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check response structure
        data = response.json()
        self.assertIn('comments', data)
        self.assertEqual(len(data['comments']), 1)  # One top-level comment
        
        # Check first level
        top_comment_data = data['comments'][0]
        self.assertEqual(top_comment_data['content'], "Top level comment")
        self.assertEqual(len(top_comment_data['replies']), 1)
        
        # Check second level
        level1_data = top_comment_data['replies'][0]
        self.assertEqual(level1_data['content'], "Level 1 reply")
        self.assertEqual(len(level1_data['replies']), 1)
        
        # Check third level
        level2_data = level1_data['replies'][0]
        self.assertEqual(level2_data['content'], "Level 2 reply")
        self.assertEqual(len(level2_data['replies']), 1)
        
        # Check fourth level
        level3_data = level2_data['replies'][0]
        self.assertEqual(level3_data['content'], "Level 3 reply")
        self.assertEqual(len(level3_data['replies']), 0)  # No more replies at this level
