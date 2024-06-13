import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Exam, Question, StudentAnswer
from main.models import Student, Course, Instructor
from main.views import is_instructor_authorised, is_student_authorised
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, F, FloatField, Q, Prefetch
from django.db.models.functions import Cast


def exam(request, code):
    try:
        course = Course.objects.get(code=code)
        if is_instructor_authorised(request, code):
            if request.method == 'POST':
                title = request.POST.get('title')
                description = request.POST.get('description')
                start = request.POST.get('start')
                end = request.POST.get('end')
                publish_status = request.POST.get('checkbox')
                exam = Exam(title=title, description=description, start=start,
                            end=end, publish_status=publish_status, course=course)
                exam.save()
                return redirect('addQuestion', code=code, exam_id=exam.id)
            else:
                return render(request, 'exam/exam.html', {'course': course, 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id'])})

        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


def addQuestion(request, code, exam_id):
    try:
        course = Course.objects.get(code=code)
        if is_instructor_authorised(request, code):
            exam = Exam.objects.get(id=exam_id)
            if request.method == 'POST':
                question = request.POST.get('question')
                option1 = request.POST.get('option1')
                option2 = request.POST.get('option2')
                option3 = request.POST.get('option3')
                option4 = request.POST.get('option4')
                answer = request.POST.get('answer')
                marks = request.POST.get('marks')
                explanation = request.POST.get('explanation')
                question = Question(question=question, option1=option1, option2=option2,
                                    option3=option3, option4=option4, answer=answer, exam=exam, marks=marks, explanation=explanation)
                question.save()
                messages.success(request, 'Question added successfully')
            else:
                return render(request, 'exam/addQuestion.html', {'course': course, 'exam': exam, 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id'])})
            if 'saveOnly' in request.POST:
                return redirect('allexams', code=code)
            return render(request, 'exam/addQuestion.html', {'course': course, 'exam': exam, 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id'])})
        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


def allexams(request, code):
    if is_instructor_authorised(request, code):
        course = Course.objects.get(code=code)
        exams = Exam.objects.filter(course=course)
        for exam in exams:
            exam.total_questions = Question.objects.filter(exam=exam).count()
            if exam.start < datetime.datetime.now():
                exam.started = True
            else:
                exam.started = False
            exam.save()
        return render(request, 'exam/allexams.html', {'course': course, 'exams': exams, 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id'])})
    else:
        return redirect('std_login')


def myexams(request, code):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        exams = Exam.objects.filter(course=course)
        student = Student.objects.get(student_id=request.session['student_id'])

        # Determine which exams are active and which are previous
        active_exams = []
        previous_exams = []
        for exam in exams:
            if exam.end < timezone.now() or exam.studentanswer_set.filter(student=student).exists():
                previous_exams.append(exam)
            else:
                active_exams.append(exam)

        # Add attempted flag to exams
        for exam in exams:
            exam.attempted = exam.studentanswer_set.filter(
                student=student).exists()

        # Add total marks obtained, percentage, and total questions for previous exams
        for exam in previous_exams:
            student_answers = exam.studentanswer_set.filter(student=student)
            total_marks_obtained = sum([student_answer.question.marks if student_answer.answer ==
                                       student_answer.question.answer else 0 for student_answer in student_answers])
            exam.total_marks_obtained = total_marks_obtained
            exam.total_marks = sum(
                [question.marks for question in exam.question_set.all()])
            exam.percentage = round(
                total_marks_obtained / exam.total_marks * 100, 2) if exam.total_marks != 0 else 0
            exam.total_questions = exam.question_set.count()

        # Add total questions for active exams
        for exam in active_exams:
            exam.total_questions = exam.question_set.count()

        return render(request, 'exam/myexams.html', {
            'course': course,
            'exams': exams,
            'active_exams': active_exams,
            'previous_exams': previous_exams,
            'student': student,
        })
    else:
        return redirect('std_login')


def startExam(request, code, exam_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        exam = Exam.objects.get(id=exam_id)
        questions = Question.objects.filter(exam=exam)
        total_questions = questions.count()

        marks = 0
        for question in questions:
            marks += question.marks
        exam.total_marks = marks

        return render(request, 'exam/portalStdNew.html', {'course': course, 'exam': exam, 'questions': questions, 'total_questions': total_questions, 'student': Student.objects.get(student_id=request.session['student_id'])})
    else:
        return redirect('std_login')


def studentAnswer(request, code, exam_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        exam = Exam.objects.get(id=exam_id)
        questions = Question.objects.filter(exam=exam)
        student = Student.objects.get(student_id=request.session['student_id'])

        for question in questions:
            answer = request.POST.get(str(question.id))
            student_answer = StudentAnswer(student=student, exam=exam, question=question,
                                           answer=answer, marks=question.marks if answer == question.answer else 0)
            # prevent duplicate answers & multiple attempts
            try:
                student_answer.save()
            except:
                redirect('myexams', code=code)
        return redirect('myexams', code=code)
    else:
        return redirect('std_login')


def examResult(request, code, exam_id):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        exam = Exam.objects.get(id=exam_id)
        questions = Question.objects.filter(exam=exam)
        try:
            student = Student.objects.get(
                student_id=request.session['student_id'])
            student_answers = StudentAnswer.objects.filter(
                student=student, exam=exam)
            total_marks_obtained = 0
            for student_answer in student_answers:
                total_marks_obtained += student_answer.question.marks if student_answer.answer == student_answer.question.answer else 0
            exam.total_marks_obtained = total_marks_obtained
            exam.total_marks = 0
            for question in questions:
                exam.total_marks += question.marks
            exam.percentage = (total_marks_obtained / exam.total_marks) * 100
            exam.percentage = round(exam.percentage, 2)
        except:
            exam.total_marks_obtained = 0
            exam.total_marks = 0
            exam.percentage = 0

        for question in questions:
            student_answer = StudentAnswer.objects.get(
                student=student, question=question)
            question.student_answer = student_answer.answer

        student_answers = StudentAnswer.objects.filter(
            student=student, exam=exam)
        for student_answer in student_answers:
            exam.time_taken = student_answer.created_at - exam.start
            exam.time_taken = exam.time_taken.total_seconds()
            exam.time_taken = round(exam.time_taken, 2)
            exam.submission_time = student_answer.created_at.strftime(
                "%a, %d-%b-%y at %I:%M %p")
        return render(request, 'exam/examResult.html', {'course': course, 'exam': exam, 'questions': questions, 'student': student})
    else:
        return redirect('std_login')


def examSummary(request, code, exam_id):
    if is_instructor_authorised(request, code):
        course = Course.objects.get(code=code)
        exam = Exam.objects.get(id=exam_id)

        questions = Question.objects.filter(exam=exam)
        time = datetime.datetime.now()
        total_students = Student.objects.filter(course=course).count()
        for question in questions:
            question.A = StudentAnswer.objects.filter(
                question=question, answer='A').count()
            question.B = StudentAnswer.objects.filter(
                question=question, answer='B').count()
            question.C = StudentAnswer.objects.filter(
                question=question, answer='C').count()
            question.D = StudentAnswer.objects.filter(
                question=question, answer='D').count()
        # students who have attempted the exam and their marks
        students = Student.objects.filter(course=course)
        for student in students:
            student_answers = StudentAnswer.objects.filter(
                student=student, exam=exam)
            total_marks_obtained = 0
            for student_answer in student_answers:
                total_marks_obtained += student_answer.question.marks if student_answer.answer == student_answer.question.answer else 0
            student.total_marks_obtained = total_marks_obtained

        if request.method == 'POST':
            exam.publish_status = True
            exam.save()
            return redirect('examSummary', code=code, exam_id=exam.id)
        # check if student has attempted the exam
        for student in students:
            if StudentAnswer.objects.filter(student=student, exam=exam).count() > 0:
                student.attempted = True
            else:
                student.attempted = False
        for student in students:
            student_answers = StudentAnswer.objects.filter(
                student=student, exam=exam)
            for student_answer in student_answers:
                student.submission_time = student_answer.created_at.strftime(
                    "%a, %d-%b-%y at %I:%M %p")

        context = {'course': course, 'exam': exam, 'questions': questions, 'time': time, 'total_students': total_students,
                   'students': students, 'instructor': Instructor.objects.get(instructor_id=request.session['instructor_id'])}
        return render(request, 'exam/examSummaryInstructor.html', context)

    else:
        return redirect('std_login')


