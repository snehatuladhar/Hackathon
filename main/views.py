import datetime
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Student, Course, Announcement, Assignment, Submission, Material, Instructor, ClassRooms
from django.template.defaulttags import register
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from .forms import AnnouncementForm, AssignmentForm, MaterialForm
from django import forms
from django.core import validators
from django.views import View
from django.shortcuts import render, redirect

from django import forms


class LoginForm(forms.Form):
    id = forms.CharField(label='ID', max_length=10, validators=[
                         validators.RegexValidator(r'^\d+$', 'Please enter a valid number.')])
    password = forms.CharField(widget=forms.PasswordInput)


def is_student_authorised(request, code):
    course = Course.objects.get(code=code)
    if request.session.get('student_id') and course in Student.objects.get(student_id=request.session['student_id']).course.all():
        return True
    else:
        return False


def is_instructor_authorised(request, code):
    if request.session.get('instructor_id') and code in Course.objects.filter(instructor_id=request.session['instructor_id']).values_list('code', flat=True):
        return True
    else:
        return False


# Custom Login page for both student and instructor
def std_login(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Student.objects.filter(student_id=id, password=password).exists():
                request.session['student_id'] = id
                return redirect('myCourses')
            elif Instructor.objects.filter(instructor_id=id, password=password).exists():
                request.session['instructor_id'] = id
                return redirect('instructorCourses')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')
    else:
        form = LoginForm()

    if 'student_id' in request.session:
        return redirect('/my/')
    elif 'instructor_id' in request.session:
        return redirect('/instructorCourses/')

    context = {'form': form, 'error_messages': error_messages}
    return render(request, 'login_page.html', context)

# Clears the session on logout


def std_logout(request):
    request.session.flush()
    return redirect('std_login')


# Display all courses (student view)
def myCourses(request):
    try:
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
            courses = student.course.all()
            instructor = student.course.all().values_list('instructor_id', flat=True)

            context = {
                'courses': courses,
                'student': student,
                'instructor': instructor
            }

            return render(request, 'main/myCourses.html', context)
        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


# Display all courses (instructor view)
def instructorCourses(request):
    try:
        if request.session['instructor_id']:
            instructor = Instructor.objects.get(
                instructor_id=request.session['instructor_id'])
            courses = Course.objects.filter(
                instructor_id=request.session['instructor_id'])
            # Student count of each course to show on the instructor page
            studentCount = Course.objects.all().annotate(student_count=Count('students'))

            studentCountDict = {}

            for course in studentCount:
                studentCountDict[course.code] = course.student_count

            @register.filter
            def get_item(dictionary, course_code):
                return dictionary.get(course_code)

            context = {
                'courses': courses,
                'instructor': instructor,
                'studentCount': studentCountDict
            }

            return render(request, 'main/instructorCourses.html', context)

        else:
            return redirect('std_login')
    except:

        return redirect('std_login')


# Particular course page (student view)
def course_page(request, code):
    # try:
    course = Course.objects.get(code=code)
    if is_student_authorised(request, code):
        try:
            announcements = Announcement.objects.filter(course_code=course)
            assignments = Assignment.objects.filter(
                course_code=course.code)
            materials = Material.objects.filter(course_code=course.code)

        except:
            announcements = None
            assignments = None
            materials = None

        context = {
            'course': course,
            'announcements': announcements,
            'assignments': assignments[:3],
            'materials': materials,
            'student': Student.objects.get(student_id=request.session['student_id'])
        }

        print(materials)

        return render(request, 'main/course.html', context)

    else:
        return redirect('std_login')
    # except:
    #     return render(request, 'error.html')


# Particular course page (instructor view)
def course_page_instructor(request, code):
    course = Course.objects.get(code=code)
    if request.session.get('instructor_id'):
        try:
            announcements = Announcement.objects.filter(course_code=course)
            assignments = Assignment.objects.filter(
                course_code=course.code)
            materials = Material.objects.filter(course_code=course.code)
            studentCount = Student.objects.filter(course=course).count()

        except:
            announcements = None
            assignments = None
            materials = None

        context = {
            'course': course,
            'announcements': announcements,
            'assignments': assignments[:3],
            'materials': materials,
            'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']),
            'studentCount': studentCount
        }

        return render(request, 'main/instructor_course.html', context)
    else:
        return redirect('std_login')


def error(request):
    return render(request, 'error.html')


# Display user profile(student & instructor)
def profile(request, id):
    try:
        if request.session['student_id'] == id:
            student = Student.objects.get(student_id=id)
            return render(request, 'main/profile.html', {'student': student})
        else:
            return redirect('std_login')
    except:
        try:
            if request.session['instructor_id'] == id:
                instructor = Instructor.objects.get(instructor_id=id)
                return render(request, 'main/instructor_profile.html', {'instructor': instructor})
            else:
                return redirect('std_login')
        except:
            return render(request, 'error.html')


def addAnnouncement(request, code):
    if is_instructor_authorised(request, code):
        if request.method == 'POST':
            form = AnnouncementForm(request.POST)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Announcement added successfully.')
                return redirect('/instructor/' + str(code))
        else:
            form = AnnouncementForm()
        return render(request, 'main/announcement.html', {'course': Course.objects.get(code=code), 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']), 'form': form})
    else:
        return redirect('std_login')


def deleteAnnouncement(request, code, id):
    if is_instructor_authorised(request, code):
        try:
            announcement = Announcement.objects.get(course_code=code, id=id)
            announcement.delete()
            messages.warning(request, 'Announcement deleted successfully.')
            return redirect('/instructor/' + str(code))
        except:
            return redirect('/instructor/' + str(code))
    else:
        return redirect('std_login')


def editAnnouncement(request, code, id):
    if is_instructor_authorised(request, code):
        announcement = Announcement.objects.get(course_code_id=code, id=id)
        form = AnnouncementForm(instance=announcement)
        context = {
            'announcement': announcement,
            'course': Course.objects.get(code=code),
            'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']),
            'form': form
        }
        return render(request, 'main/update-announcement.html', context)
    else:
        return redirect('std_login')


def updateAnnouncement(request, code, id):
    if is_instructor_authorised(request, code):
        try:
            announcement = Announcement.objects.get(course_code_id=code, id=id)
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                messages.info(request, 'Announcement updated successfully.')
                return redirect('/instructor/' + str(code))
        except:
            return redirect('/instructor/' + str(code))

    else:
        return redirect('std_login')


def addAssignment(request, code):
    if is_instructor_authorised(request, code):
        if request.method == 'POST':
            form = AssignmentForm(request.POST, request.FILES)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'Assignment added successfully.')
                return redirect('/instructor/' + str(code))
        else:
            form = AssignmentForm()
        return render(request, 'main/assignment.html', {'course': Course.objects.get(code=code), 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']), 'form': form})
    else:
        return redirect('std_login')


def assignmentPage(request, code, id):
    course = Course.objects.get(code=code)
    if is_student_authorised(request, code):
        assignment = Assignment.objects.get(course_code=course.code, id=id)
        try:

            submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                student_id=request.session['student_id']))

            context = {
                'assignment': assignment,
                'course': course,
                'submission': submission,
                'time': datetime.datetime.now(),
                'student': Student.objects.get(student_id=request.session['student_id']),
                'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
            }

            return render(request, 'main/assignment-portal.html', context)

        except:
            submission = None

        context = {
            'assignment': assignment,
            'course': course,
            'submission': submission,
            'time': datetime.datetime.now(),
            'student': Student.objects.get(student_id=request.session['student_id']),
            'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
        }

        return render(request, 'main/assignment-portal.html', context)
    else:

        return redirect('std_login')


def allAssignments(request, code):
    if is_instructor_authorised(request, code):
        course = Course.objects.get(code=code)
        assignments = Assignment.objects.filter(course_code=course)
        studentCount = Student.objects.filter(course=course).count()

        context = {
            'assignments': assignments,
            'course': course,
            'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']),
            'studentCount': studentCount

        }
        return render(request, 'main/all-assignments.html', context)
    else:
        return redirect('std_login')


def allAssignmentsSTD(request, code):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        assignments = Assignment.objects.filter(course_code=course)
        context = {
            'assignments': assignments,
            'course': course,
            'student': Student.objects.get(student_id=request.session['student_id']),

        }
        return render(request, 'main/all-assignments-std.html', context)
    else:
        return redirect('std_login')


def addSubmission(request, code, id):
    try:
        course = Course.objects.get(code=code)
        if is_student_authorised(request, code):
            # check if assignment is open
            assignment = Assignment.objects.get(course_code=course.code, id=id)
            if assignment.deadline < datetime.datetime.now():

                return redirect('/assignment/' + str(code) + '/' + str(id))

            if request.method == 'POST' and request.FILES['file']:
                assignment = Assignment.objects.get(
                    course_code=course.code, id=id)
                submission = Submission(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']), file=request.FILES['file'],)
                submission.status = 'Submitted'
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(
                    course_code=course.code, id=id)
                submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']))
                context = {
                    'assignment': assignment,
                    'course': course,
                    'submission': submission,
                    'time': datetime.datetime.now(),
                    'student': Student.objects.get(student_id=request.session['student_id']),
                    'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
                }

                return render(request, 'main/assignment-portal.html', context)
        else:
            return redirect('std_login')
    except:
        return HttpResponseRedirect(request.path_info)


def viewSubmission(request, code, id):
    course = Course.objects.get(code=code)
    if is_instructor_authorised(request, code):
        try:
            assignment = Assignment.objects.get(course_code_id=code, id=id)
            submissions = Submission.objects.filter(
                assignment_id=assignment.id)

            context = {
                'course': course,
                'submissions': submissions,
                'assignment': assignment,
                'totalStudents': len(Student.objects.filter(course=course)),
                'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']),
                'courses': Course.objects.filter(instructor_id=request.session['instructor_id'])
            }

            return render(request, 'main/assignment-view.html', context)

        except:
            return redirect('/instructor/' + str(code))
    else:
        return redirect('std_login')


def gradeSubmission(request, code, id, sub_id):
    try:
        course = Course.objects.get(code=code)
        if is_instructor_authorised(request, code):
            if request.method == 'POST':
                assignment = Assignment.objects.get(course_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)
                submission.marks = request.POST['marks']
                if request.POST['marks'] == 0:
                    submission.marks = 0
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(course_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)

                context = {
                    'course': course,
                    'submissions': submissions,
                    'assignment': assignment,
                    'totalStudents': len(Student.objects.filter(course=course)),
                    'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']),
                    'courses': Course.objects.filter(instructor_id=request.session['instructor_id'])
                }

                return render(request, 'main/assignment-view.html', context)

        else:
            return redirect('std_login')
    except:
        return redirect('/error/')


def addCourseMaterial(request, code):
    if is_instructor_authorised(request, code):
        if request.method == 'POST':
            form = MaterialForm(request.POST, request.FILES)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'New course material added')
                return redirect('/instructor/' + str(code))
            else:
                return render(request, 'main/course-material.html', {'course': Course.objects.get(code=code), 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']), 'form': form})
        else:
            form = MaterialForm()
            return render(request, 'main/course-material.html', {'course': Course.objects.get(code=code), 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id']), 'form': form})
    else:
        return redirect('std_login')

def courseMaterial(request, code, id):
    if request.session.get('student_id') or request.session.get('faculty_id'):
        material = Material.objects.get(course_code=code, id=id)
        course = Course.objects.get(code=code)
        print(material)
        # courses = Course.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('faculty_id'):
            faculty = Instructor.objects.get(
                faculty_id=request.session['faculty_id'])
        else:
            faculty = None

        # enrolled = student.course.all() if student else None
        # accessed = Course.objects.filter(
        #     faculty_id=faculty.faculty_id) if faculty else None
        # if is_faculty_authorised(request, code):
        context = {
            'material': material,
            'faculty': faculty,
            'course': course,
            # 'courses': courses,
            'student': student,
            # 'enrolled': enrolled,
            # 'accessed': accessed
        }

        return render(request, 'main/material.html', context)
            # form = MaterialForm()
            # # print(form)
            # return render(request, 'main/course-material.html', {'course': Course.objects.get(code=code), 'faculty': Instructor.objects.get(faculty_id=request.session['faculty_id']), 'form': form})
    else:
        return redirect('std_login')

def editCourseMaterial(request, code, id):
    if request.session.get('faculty_id'):
        instance = Material.objects.get(id=id)
        if request.method == "POST":
            # form = MyModelForm(request.POST, instance=instance)
            form = MaterialForm(request.POST or None, instance=instance)
            if form.is_valid():
                form.save()
                print("in valid1")
                return redirect("viewCourseMaterial", code, id)
            # else:
            #     return render(request, 'main/editMaterial.html', context)
            # return render(request, 'my_template.html', {'form': form}) 

            # return render(request, 'main/editMaterial.html', context)
        else:
            faculty = Instructor.objects.get(
                faculty_id=request.session['faculty_id'])
            form = MaterialForm(request.POST or None, instance=instance)
            course = Course.objects.get(code=code)
            context = {
                'course': course,
                'material': instance,
                'form': form,
                'faculty': faculty
            }
            # return redirect("viewCourseMaterial", code, id)
            return render(request, 'main/editMaterial.html', context)
            # form = MaterialForm(instance=instance)
    else:
        return redirect('std_login')

def deleteCourseMaterial(request, code, id):
    if is_instructor_authorised(request, code):
        course = Course.objects.get(code=code)
        course_material = Material.objects.get(course_code=course, id=id)
        course_material.delete()
        messages.warning(request, 'Course material deleted')
        return redirect('/instructor/' + str(code))
    else:
        return redirect('std_login')


def courses(request):
    if request.session.get('student_id') or request.session.get('instructor_id'):

        courses = Course.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('instructor_id'):
            instructor = Instructor.objects.get(
                instructor_id=request.session['instructor_id'])
        else:
            instructor = None

        enrolled = student.course.all() if student else None
        accessed = Course.objects.filter(
            instructor_id=instructor.instructor_id) if instructor else None

        context = {
            'instructor': instructor,
            'courses': courses,
            'student': student,
            'enrolled': enrolled,
            'accessed': accessed
        }

        return render(request, 'main/all-courses.html', context)

    else:
        return redirect('std_login')


def classes(request):
    if request.session.get('student_id') or request.session.get('instructor_id'):
        classes = ClassRooms.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('instructor_id'):
            instructor = Instructor.objects.get(
                instructor_id=request.session['instructor_id'])
        else:
            instructor = None
        context = {
            'instructor': instructor,
            'student': student,
            'deps': classes
        }

        return render(request, 'main/classes.html', context)

    else:
        return redirect('std_login')


def access(request, code):
    if request.session.get('student_id'):
        course = Course.objects.get(code=code)
        student = Student.objects.get(student_id=request.session['student_id'])
        if request.method == 'POST':
            if (request.POST['key']) == str(course.studentKey):
                student.course.add(course)
                student.save()
                return redirect('/my/')
            else:
                messages.error(request, 'Invalid key')
                return HttpResponseRedirect(request.path_info)
        else:
            return render(request, 'main/access.html', {'course': course, 'student': student})

    else:
        return redirect('std_login')


def search(request):
    if request.session.get('student_id') or request.session.get('instructor_id'):
        if request.method == 'GET' and request.GET['q']:
            q = request.GET['q']
            courses = Course.objects.filter(Q(code__icontains=q) | Q(
                name__icontains=q) | Q(instructor__name__icontains=q))

            if request.session.get('student_id'):
                student = Student.objects.get(
                    student_id=request.session['student_id'])
            else:
                student = None
            if request.session.get('instructor_id'):
                instructor = Instructor.objects.get(
                    instructor_id=request.session['instructor_id'])
            else:
                instructor = None
            enrolled = student.course.all() if student else None
            accessed = Course.objects.filter(
                instructor_id=instructor.instructor_id) if instructor else None

            context = {
                'courses': courses,
                'instructor': instructor,
                'student': student,
                'enrolled': enrolled,
                'accessed': accessed,
                'q': q
            }
            return render(request, 'main/search.html', context)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('std_login')


def changePasswordPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePassword.html', {'student': student})
    elif request.session.get('instructor_id'):
        instructor = Instructor.objects.get(instructor_id=request.session['instructor_id'])
        return render(request, 'main/changePasswordInstructor.html', {'instructor': instructor})
    else:
        return redirect('std_login')


def changePhotoPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePhoto.html', {'student': student})
    elif request.session.get('instructor_id'):
        instructor = Instructor.objects.get(instructor_id=request.session['instructor_id'])
        return render(request, 'main/changePhotoInstructor.html', {'instructor': instructor})
    else:
        return redirect('std_login')


def changePassword(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if student.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                student.password = request.POST['newPassword']
                student.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePassword/')
        else:
            return render(request, 'main/changePassword.html', {'student': student})
    else:
        return redirect('std_login')


def changePasswordInstructor(request):
    if request.session.get('instructor_id'):
        instructor = Instructor.objects.get(
            instructor_id=request.session['instructor_id'])
        if request.method == 'POST':
            if instructor.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                instructor.password = request.POST['newPassword']
                instructor.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/instructorProfile/' + str(instructor.instructor_id))
            else:
                print('error')
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePasswordInstructor/')
        else:
            print(instructor)
            return render(request, 'main/changePasswordInstructor.html', {'instructor': instructor})
    else:
        return redirect('std_login')


def changePhoto(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                student.photo = request.FILES['photo']
                student.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhoto/')
        else:
            return render(request, 'main/changePhoto.html', {'student': student})
    else:
        return redirect('std_login')


def changePhotoInstructor(request):
    if request.session.get('instructor_id'):
        instructor = Instructor.objects.get(
            instructor_id=request.session['instructor_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                instructor.photo = request.FILES['photo']
                instructor.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/instructorProfile/' + str(instructor.instructor_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhotoInstructor/')
        else:
            return render(request, 'main/changePhotoInstructor.html', {'instructor': instructor})
    else:
        return redirect('std_login')


def guestStudent(request):
    request.session.flush()
    try:
        student = Student.objects.get(name='Guest Student')
        request.session['student_id'] = str(student.student_id)
        return redirect('myCourses')
    except:
        return redirect('std_login')


def guestInstructor(request):
    request.session.flush()
    try:
        instructor = Instructor.objects.get(name='Guest Instructor')
        request.session['instructor_id'] = str(instructor.instructor_id)
        return redirect('instructorCourses')
    except:
        return redirect('std_login')
    


class TeacherLoginForm(forms.Form):
    id = forms.CharField(label='ID', max_length=10, validators=[
                         validators.RegexValidator(r'^\d+$', 'Please enter a valid number.')])
    password = forms.CharField(widget=forms.PasswordInput)

class TeacherLoginView(View):
    def get(self, request):
        form = TeacherLoginForm()
        return render(request, 'teacher_login.html', {'form': form})

    def post(self, request):
        error_messages = []
        form = TeacherLoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Instructor.objects.filter(instructor_id=id, password=password).exists():
                request.session['instructor_id'] = id
                return redirect('instructorCourses')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')

        context = {'form': form, 'error_messages': error_messages}
        return render(request, 'teacher_login.html', context)
