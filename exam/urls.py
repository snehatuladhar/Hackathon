from django.urls import path
from . import views

urlpatterns = [
    path('exam/<int:code>', views.exam, name='exam'),
    path('addQuestion/<int:code>/<int:exam_id>', views.addQuestion, name='addQuestion'),
    path('allexams/<int:code>', views.allexams, name='allexams'),
    path('examSummary/<int:code>/<int:exam_id>', views.examSummary, name='examSummary'),
    path('myexams/<int:code>', views.myexams, name='myexams'),
    path('startExam/<int:code>/<int:exam_id>', views.startExam, name='startExam'),
    path('studentAnswer/<int:code>/<int:exam_id>', views.studentAnswer, name='studentAnswer'),
    path('examResult/<int:code>/<int:exam_id>', views.examResult, name='examResult'),
  
]