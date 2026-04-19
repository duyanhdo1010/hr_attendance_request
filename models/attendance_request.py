from odoo import fields, models
from odoo.exceptions import UserError


class AttendanceRequest(models.Model):
    _name = 'attendance.request'
    _description = 'Forgot Attendance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', copy=False)
    name = fields.Char(string='Mã đơn', default='New', copy=False)
    employee_id = fields.Many2one(
        'hr.employee', 
        string='Nhân viên', 
        required=True, 
        related='hr_employee.name',
        store=True
    )
    request_date = fields.Date(
        string='Ngày tạo', default=fields.Date.context_today,
    )
    pm_id = fields.Many2one(
        'hr.employee', 
        string='Quản lý trực tiếp', 
        required=True,
        related="hr_employee.name",
        store=True
    )
    state = fields.Selection(
        [
            ('draft', 'Nháp'),
            ('pm_approve', 'Chờ PM duyệt'),
            ('dl_approve', 'Chờ DL duyệt'),
            ('hr_approve', 'Chờ HR duyệt'),
            ('approved', 'Đã duyệt'),
            ('rejected', 'Từ chối'),
        ],
        string='Trạng thái',
        default='draft',
        tracking=True,
    )
    line_ids = fields.One2many(
        'attendance.request.line',
        'request_id',
        string='Attendance Request Lines',
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True
    )

    note = fields.Text("Note")
    commit_checkbox = fields.Boolean(string="")

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("You don't have permisson to do this action")
            else:
                record.state = 'pm_approve'
