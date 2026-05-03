{
    'name': 'Forgot Attendance Request',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage employee forgotten attendance requests',
    'depends':['base', 'hr', 'mail'],
    'data':[
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/ir_sequence_data.xml',
        'wizard/attendance_reject_wizard_views.xml',
        'views/attendance_request_views.xml',
    ],
    'installable': True,
    'application': True,
}