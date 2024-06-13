from django.shortcuts import redirect, render
from discussion.models import InstructorDiscussion, StudentDiscussion
from main.models import Student, Instructor, Course
from main.views import is_instructor_authorised, is_student_authorised
from itertools import chain
from .forms import StudentDiscussionForm, InstructorDiscussionForm


# Create your views here.


''' We have two different user models.
    That's why we are filtering the discussions based on the user type and then combining them.'''


def context_list(course):
    try:
        studentDis = StudentDiscussion.objects.filter(course=course)
        instructorDis = InstructorDiscussion.objects.filter(course=course)
        discussions = list(chain(studentDis, instructorDis))
        discussions.sort(key=lambda x: x.sent_at, reverse=True)

        for dis in discussions:
            if dis.__class__.__name__ == 'StudentDiscussion':
                dis.author = Student.objects.get(student_id=dis.sent_by_id)
            else:
                dis.author = Instructor.objects.get(instructor_id=dis.sent_by_id)
    except:

        discussions = []

    return discussions


def discussion(request, code):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        student = Student.objects.get(student_id=request.session['student_id'])
        discussions = context_list(course)
        form = StudentDiscussionForm()
        context = {
            'course': course,
            'student': student,
            'discussions': discussions,
            'form': form,
        }
        return render(request, 'discussion/discussion.html', context)

    elif is_instructor_authorised(request, code):
        course = Course.objects.get(code=code)
        instructor = Instructor.objects.get(instructor_id=request.session['instructor_id'])
        discussions = context_list(course)
        form = InstructorDiscussionForm()
        context = {
            'course': course,
            'instructor': instructor,
            'discussions': discussions,
            'form': form,
        }
        return render(request, 'discussion/discussion.html', context)
    else:
        return redirect('std_login')


def send(request, code, std_id):
    if is_student_authorised(request, code):
        if request.method == 'POST':
            form = StudentDiscussionForm(request.POST)
            if form.is_valid():
                content = form.cleaned_data['content']
                course = Course.objects.get(code=code)
                try:
                    student = Student.objects.get(student_id=std_id)
                except:
                    return redirect('discussion', code=code)
                StudentDiscussion.objects.create(
                    content=content, course=course, sent_by=student)
                return redirect('discussion', code=code)
            else:
                return redirect('discussion', code=code)
        else:
            return redirect('discussion', code=code)
    else:
        return render(request, 'std_login.html')


def send_fac(request, code, fac_id):
    if is_instructor_authorised(request, code):
        if request.method == 'POST':
            form = InstructorDiscussionForm(request.POST)
            if form.is_valid():
                content = form.cleaned_data['content']
                course = Course.objects.get(code=code)
                try:
                    instructor = Instructor.objects.get(instructor_id=fac_id)
                except:
                    return redirect('discussion', code=code)
                InstructorDiscussion.objects.create(
                    content=content, course=course, sent_by=instructor)
                return redirect('discussion', code=code)
            else:
                return redirect('discussion', code=code)
        else:
            return redirect('discussion', code=code)
    else:
        return render(request, 'std_login.html')
