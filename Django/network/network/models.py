from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, default='')


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(max_length=280)
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."

    class Meta:
        ordering = ['-timestamp']


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=280)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    is_edited = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} on {self.post}: {self.content[:30]}..."

    class Meta:
        ordering = ['timestamp']


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'followed']


class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions", null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="reactions", null=True, blank=True)
    emoji = models.CharField(max_length=10)  # Store the unicode emoji character
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['user', 'post', 'emoji'],
            ['user', 'comment', 'emoji']
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False, comment__isnull=True) | 
                    models.Q(post__isnull=True, comment__isnull=False)
                ),
                name="reaction_post_or_comment"
            )
        ]

    def __str__(self):
        target = self.post if self.post else self.comment
        return f"{self.user.username} reacted with {self.emoji} on {target}"
