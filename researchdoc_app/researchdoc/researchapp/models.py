"""
All the database tables for ResearchDoc.

Each Python class is one SQL table. Each class attribute is one column.
The links between tables (ForeignKey, OneToOneField) describe how rows
in one table point at rows in another.

The chain of ownership looks like:
    User -> UserDetail
         -> Subscription
         -> ResearchProject -> Resource
                            -> ResearchSummary -> Citation -> Resource
                            -> ComparisonTable -> Column / Row / Cell

Everything cascades on delete from the top down. So if you delete a User
their projects vanish, and with each project goes its resources,
summaries, citations and comparison tables.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.firstname or self.surname:
            return f"{self.firstname} {self.surname}".strip()
        return self.user.username
