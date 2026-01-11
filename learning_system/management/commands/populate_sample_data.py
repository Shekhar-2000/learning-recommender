from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from learning_system.models import (
    Course, Lesson, Quiz, Question, Answer,
    AssessmentQuiz, AssessmentQuestion, AssessmentAnswer, AssessmentResult,
    StudentProfile, TeacherProfile, QuizPerformance, Engagement
)
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample courses
        self.create_courses()
        
        # Create sample users
        self.create_users()
        
        # Create assessment data
        self.create_assessment_data()
        
        # Create sample performance data
        self.create_performance_data()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_courses(self):
        """Create sample courses with lessons and quizzes"""
        courses_data = [
            {
                'title': 'Python Programming Fundamentals',
                'description': 'Learn the basics of Python programming from scratch. Perfect for beginners who want to start their coding journey.',
                'tags': 'python,programming,beginner,coding'
            },
            {
                'title': 'Web Development with Django',
                'description': 'Build dynamic web applications using Django framework. Learn backend development and database management.',
                'tags': 'django,web-development,backend,python'
            },
            {
                'title': 'Machine Learning Basics',
                'description': 'Introduction to machine learning concepts, algorithms, and practical applications using Python.',
                'tags': 'machine-learning,ai,data-science,python'
            },
            {
                'title': 'JavaScript and React',
                'description': 'Master modern JavaScript and React for building interactive web applications.',
                'tags': 'javascript,react,frontend,web-development'
            },
            {
                'title': 'Data Structures and Algorithms',
                'description': 'Learn fundamental computer science concepts including data structures and algorithmic thinking.',
                'tags': 'algorithms,data-structures,computer-science,programming'
            },
            {
                'title': 'Database Design and SQL',
                'description': 'Master database design principles and SQL for efficient data management.',
                'tags': 'sql,database,data-management,backend'
            }
        ]

        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'description': course_data['description'],
                    'tags': course_data['tags']
                }
            )
            
            if created:
                # Create lessons for each course
                self.create_lessons_for_course(course)
                self.stdout.write(f'Created course: {course.title}')

    def create_lessons_for_course(self, course):
        """Create lessons and quizzes for a course"""
        lesson_templates = {
            'Python Programming Fundamentals': [
                {'title': 'Introduction to Python', 'content': 'Learn about Python syntax and basic concepts.'},
                {'title': 'Variables and Data Types', 'content': 'Understanding different data types in Python.'},
                {'title': 'Control Structures', 'content': 'If statements, loops, and conditional logic.'},
                {'title': 'Functions and Modules', 'content': 'Creating and using functions in Python.'}
            ],
            'Web Development with Django': [
                {'title': 'Django Basics', 'content': 'Introduction to Django framework and MVC pattern.'},
                {'title': 'Models and Database', 'content': 'Creating models and working with databases.'},
                {'title': 'Views and Templates', 'content': 'Building views and creating templates.'},
                {'title': 'URLs and Routing', 'content': 'URL patterns and routing in Django.'}
            ],
            'Machine Learning Basics': [
                {'title': 'Introduction to ML', 'content': 'What is machine learning and its applications.'},
                {'title': 'Data Preprocessing', 'content': 'Cleaning and preparing data for ML models.'},
                {'title': 'Supervised Learning', 'content': 'Classification and regression algorithms.'},
                {'title': 'Model Evaluation', 'content': 'How to evaluate and improve ML models.'}
            ],
            'JavaScript and React': [
                {'title': 'JavaScript Fundamentals', 'content': 'ES6+ features and modern JavaScript.'},
                {'title': 'React Components', 'content': 'Building reusable React components.'},
                {'title': 'State Management', 'content': 'Managing component state and props.'},
                {'title': 'React Hooks', 'content': 'Using hooks for functional components.'}
            ],
            'Data Structures and Algorithms': [
                {'title': 'Arrays and Lists', 'content': 'Working with arrays and linked lists.'},
                {'title': 'Sorting Algorithms', 'content': 'Bubble sort, quick sort, and merge sort.'},
                {'title': 'Searching Algorithms', 'content': 'Linear search, binary search, and hash tables.'},
                {'title': 'Tree Structures', 'content': 'Binary trees, BST, and tree traversal.'}
            ],
            'Database Design and SQL': [
                {'title': 'Database Concepts', 'content': 'Understanding relational databases.'},
                {'title': 'SQL Basics', 'content': 'SELECT, INSERT, UPDATE, DELETE operations.'},
                {'title': 'Joins and Relationships', 'content': 'Working with multiple tables.'},
                {'title': 'Database Optimization', 'content': 'Indexing and query optimization.'}
            ]
        }

        lessons_data = lesson_templates.get(course.title, [
            {'title': 'Introduction', 'content': 'Introduction to the course topic.'},
            {'title': 'Basic Concepts', 'content': 'Understanding fundamental concepts.'},
            {'title': 'Practical Applications', 'content': 'Real-world applications and examples.'},
            {'title': 'Advanced Topics', 'content': 'Advanced concepts and best practices.'}
        ])

        for i, lesson_data in enumerate(lessons_data):
            lesson = Lesson.objects.create(
                course=course,
                title=lesson_data['title'],
                content=lesson_data['content']
            )
            
            # Create a quiz for each lesson
            quiz = Quiz.objects.create(
                lesson=lesson,
                title=f'{lesson.title} Quiz'
            )
            
            # Create questions for the quiz
            self.create_quiz_questions(quiz, course.title)

    def create_quiz_questions(self, quiz, course_title):
        """Create questions and answers for a quiz"""
        question_templates = {
            'Python Programming Fundamentals': [
                {
                    'text': 'What is the correct way to create a variable in Python?',
                    'answers': [
                        {'text': 'var x = 5', 'is_correct': False},
                        {'text': 'x = 5', 'is_correct': True},
                        {'text': 'int x = 5', 'is_correct': False},
                        {'text': 'x := 5', 'is_correct': False}
                    ]
                },
                {
                    'text': 'Which data type is used to store text in Python?',
                    'answers': [
                        {'text': 'str', 'is_correct': True},
                        {'text': 'text', 'is_correct': False},
                        {'text': 'string', 'is_correct': False},
                        {'text': 'char', 'is_correct': False}
                    ]
                }
            ],
            'Web Development with Django': [
                {
                    'text': 'What is Django?',
                    'answers': [
                        {'text': 'A programming language', 'is_correct': False},
                        {'text': 'A web framework', 'is_correct': True},
                        {'text': 'A database', 'is_correct': False},
                        {'text': 'An operating system', 'is_correct': False}
                    ]
                },
                {
                    'text': 'Which file contains Django project settings?',
                    'answers': [
                        {'text': 'settings.py', 'is_correct': True},
                        {'text': 'config.py', 'is_correct': False},
                        {'text': 'django.py', 'is_correct': False},
                        {'text': 'main.py', 'is_correct': False}
                    ]
                }
            ],
            'Machine Learning Basics': [
                {
                    'text': 'What is supervised learning?',
                    'answers': [
                        {'text': 'Learning without labels', 'is_correct': False},
                        {'text': 'Learning with labeled data', 'is_correct': True},
                        {'text': 'Learning from rewards', 'is_correct': False},
                        {'text': 'Learning without data', 'is_correct': False}
                    ]
                },
                {
                    'text': 'Which algorithm is used for classification?',
                    'answers': [
                        {'text': 'Linear Regression', 'is_correct': False},
                        {'text': 'Decision Tree', 'is_correct': True},
                        {'text': 'K-Means', 'is_correct': False},
                        {'text': 'PCA', 'is_correct': False}
                    ]
                }
            ]
        }

        questions_data = question_templates.get(course_title, [
            {
                'text': 'What is the main topic of this lesson?',
                'answers': [
                    {'text': 'Option A', 'is_correct': True},
                    {'text': 'Option B', 'is_correct': False},
                    {'text': 'Option C', 'is_correct': False},
                    {'text': 'Option D', 'is_correct': False}
                ]
            },
            {
                'text': 'Which statement is correct?',
                'answers': [
                    {'text': 'Statement 1', 'is_correct': False},
                    {'text': 'Statement 2', 'is_correct': True},
                    {'text': 'Statement 3', 'is_correct': False},
                    {'text': 'Statement 4', 'is_correct': False}
                ]
            }
        ])

        for question_data in questions_data:
            question = Question.objects.create(
                quiz=quiz,
                text=question_data['text']
            )
            
            for answer_data in question_data['answers']:
                Answer.objects.create(
                    question=question,
                    text=answer_data['text'],
                    is_correct=answer_data['is_correct']
                )

    def create_users(self):
        """Create sample users (students and teachers)"""
        # Create students
        students_data = [
            {'username': 'alice_student', 'email': 'alice@example.com', 'first_name': 'Alice', 'last_name': 'Johnson'},
            {'username': 'bob_student', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Smith'},
            {'username': 'carol_student', 'email': 'carol@example.com', 'first_name': 'Carol', 'last_name': 'Davis'},
            {'username': 'david_student', 'email': 'david@example.com', 'first_name': 'David', 'last_name': 'Wilson'},
            {'username': 'eve_student', 'email': 'eve@example.com', 'first_name': 'Eve', 'last_name': 'Brown'}
        ]

        for student_data in students_data:
            user, created = User.objects.get_or_create(
                username=student_data['username'],
                defaults={
                    'email': student_data['email'],
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'is_student': True,
                    'is_teacher': False
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                StudentProfile.objects.create(user=user)
                self.stdout.write(f'Created student: {user.username}')

        # Create teachers
        teachers_data = [
            {'username': 'prof_smith', 'email': 'prof.smith@university.edu', 'first_name': 'Dr. John', 'last_name': 'Smith'},
            {'username': 'prof_jones', 'email': 'prof.jones@university.edu', 'first_name': 'Dr. Sarah', 'last_name': 'Jones'}
        ]

        for teacher_data in teachers_data:
            user, created = User.objects.get_or_create(
                username=teacher_data['username'],
                defaults={
                    'email': teacher_data['email'],
                    'first_name': teacher_data['first_name'],
                    'last_name': teacher_data['last_name'],
                    'is_student': False,
                    'is_teacher': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                TeacherProfile.objects.create(user=user)
                self.stdout.write(f'Created teacher: {user.username}')

    def create_assessment_data(self):
        """Create assessment quiz and questions"""
        assessment, created = AssessmentQuiz.objects.get_or_create(
            title="Initial Learning Assessment",
            defaults={
                'description': 'Complete this assessment to get personalized course recommendations.',
                'is_active': True
            }
        )

        if created:
            # Create assessment questions
            assessment_questions = [
                {
                    'text': 'What is your programming experience level?',
                    'category': 'programming',
                    'difficulty_level': 1,
                    'answers': [
                        {'text': 'Complete beginner', 'skill_points': {'programming': 10, 'beginner': 20}},
                        {'text': 'Some experience', 'skill_points': {'programming': 30, 'intermediate': 20}},
                        {'text': 'Intermediate', 'skill_points': {'programming': 50, 'intermediate': 30}},
                        {'text': 'Advanced', 'skill_points': {'programming': 80, 'advanced': 40}}
                    ]
                },
                {
                    'text': 'Which programming language interests you most?',
                    'category': 'preference',
                    'difficulty_level': 1,
                    'answers': [
                        {'text': 'Python', 'skill_points': {'python': 30, 'programming': 20}},
                        {'text': 'JavaScript', 'skill_points': {'javascript': 30, 'web-development': 20}},
                        {'text': 'Java', 'skill_points': {'java': 30, 'programming': 20}},
                        {'text': 'C++', 'skill_points': {'c++': 30, 'programming': 20}}
                    ]
                },
                {
                    'text': 'What type of projects interest you?',
                    'category': 'preference',
                    'difficulty_level': 2,
                    'answers': [
                        {'text': 'Web Development', 'skill_points': {'web-development': 40, 'frontend': 20}},
                        {'text': 'Data Science', 'skill_points': {'data-science': 40, 'analytics': 20}},
                        {'text': 'Mobile Apps', 'skill_points': {'mobile': 40, 'app-development': 20}},
                        {'text': 'Game Development', 'skill_points': {'game-development': 40, 'gaming': 20}}
                    ]
                },
                {
                    'text': 'How do you prefer to learn?',
                    'category': 'learning_style',
                    'difficulty_level': 1,
                    'answers': [
                        {'text': 'Hands-on coding', 'skill_points': {'practical': 30, 'coding': 20}},
                        {'text': 'Reading documentation', 'skill_points': {'theoretical': 30, 'research': 20}},
                        {'text': 'Video tutorials', 'skill_points': {'visual': 30, 'multimedia': 20}},
                        {'text': 'Interactive exercises', 'skill_points': {'interactive': 30, 'practice': 20}}
                    ]
                },
                {
                    'text': 'What is your goal with programming?',
                    'category': 'goal',
                    'difficulty_level': 2,
                    'answers': [
                        {'text': 'Career change', 'skill_points': {'career': 40, 'professional': 20}},
                        {'text': 'Personal projects', 'skill_points': {'personal': 40, 'hobby': 20}},
                        {'text': 'Academic study', 'skill_points': {'academic': 40, 'research': 20}},
                        {'text': 'Entrepreneurship', 'skill_points': {'business': 40, 'startup': 20}}
                    ]
                }
            ]

            for q_data in assessment_questions:
                question = AssessmentQuestion.objects.create(
                    assessment=assessment,
                    text=q_data['text'],
                    category=q_data['category'],
                    difficulty_level=q_data['difficulty_level']
                )
                
                for a_data in q_data['answers']:
                    AssessmentAnswer.objects.create(
                        question=question,
                        text=a_data['text'],
                        skill_points=a_data['skill_points']
                    )

            self.stdout.write('Created assessment quiz with questions')

    def create_performance_data(self):
        """Create sample performance data for students"""
        students = StudentProfile.objects.all()
        courses = Course.objects.all()
        
        if not students.exists() or not courses.exists():
            self.stdout.write('No students or courses found. Skipping performance data.')
            return

        for student in students:
            # Create some assessment results
            assessment = AssessmentQuiz.objects.first()
            if assessment:
                skill_scores = {
                    'programming': random.randint(20, 80),
                    'python': random.randint(10, 70),
                    'web-development': random.randint(15, 75),
                    'beginner': random.randint(30, 90)
                }
                
                learning_level = random.choice(['beginner', 'intermediate', 'advanced'])
                recommended_courses = list(courses.values_list('id', flat=True))[:3]
                
                AssessmentResult.objects.get_or_create(
                    student=student,
                    assessment=assessment,
                    defaults={
                        'total_score': sum(skill_scores.values()),
                        'skill_scores': skill_scores,
                        'recommended_courses': recommended_courses,
                        'learning_level': learning_level
                    }
                )

            # Create quiz performances
            quizzes = Quiz.objects.all()
            for quiz in quizzes[:random.randint(3, 8)]:  # Random number of quizzes per student
                score = random.randint(40, 100)
                time_spent = random.randint(60, 300)  # 1-5 minutes
                
                QuizPerformance.objects.get_or_create(
                    student=student,
                    quiz=quiz,
                    defaults={
                        'score': score,
                        'time_spent_seconds': time_spent
                    }
                )

            # Create engagement data
            lessons = Lesson.objects.all()
            for lesson in lessons[:random.randint(2, 6)]:  # Random number of lessons per student
                time_spent = random.randint(300, 1800)  # 5-30 minutes
                completion_status = random.choice(['completed', 'in_progress', 'not_started'])
                
                Engagement.objects.get_or_create(
                    student=student,
                    lesson=lesson,
                    defaults={
                        'time_spent_seconds': time_spent,
                        'completion_status': completion_status
                    }
                )

        self.stdout.write('Created sample performance data')
