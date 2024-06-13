from django.contrib import admin

# Register your models here.
from .models import Student, Instructor, Course, ClassRooms, Assignment, Announcement

admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Course)
admin.site.register(ClassRooms)
admin.site.register(Assignment)
admin.site.register(Announcement)
