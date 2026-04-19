{
    'name': 'Forgot Attendance Request',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Quản lý request quên chấm công của nhân viên',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_request_views.xml',
    ],
    'installable': True,
    'application': True,
}
