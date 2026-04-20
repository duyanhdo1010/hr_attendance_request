from odoo import fields, models, api
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
        default=lambda self: self.env.user.employee_ids[:1]
    )
    request_date = fields.Date(string='Ngày tạo', default=fields.Date.context_today)
    pm_id = fields.Many2one('hr.employee', string='Quản lý trực tiếp', required=True)
    dl_id = fields.Many2one('hr.employee', string='Department Lead', required=True)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pm_approve', 'Chờ PM duyệt'),
        ('dl_approve', 'Chờ DL duyệt'),
        ('hr_approve', 'Chờ HR duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string='Trạng thái', default='draft', track_visibility='onchange')
    
    line_ids = fields.One2many('attendance.request.line', 'request_id', string='Chi tiết')

    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department_id', store=True)

    note = fields.Text("Note")
    commit_checkbox = fields.Boolean(string="I commit that the provided information is accurate")

    @api.depends('employee_id', 'employee_id.department_id')
    def _compute_department_id(self):
        for record in self:
            record.department_id = record.employee_id.department_id if record.employee_id else False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.pm_id = self.employee_id.parent_id
            if self.employee_id.department_id:
                self.dl_id = self.employee_id.department_id.manager_id
        else:
            self.pm_id = False
            self.dl_id = False

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                raise UserError("You don't have permission to do this action")
            if not record.commit_checkbox:
                raise UserError("You need to commit before Submit!")
            record.state = 'pm_approve'

    def action_approve(self):
        current_employee = self.env.user.employee_ids[:1]
        for record in self:
            if record.state == 'pm_approve':
                if current_employee != record.pm_id:
                    raise UserError("Only the Project Manager can approve this request!")
                record.state = 'dl_approve'
            elif record.state == 'dl_approve':
                if current_employee != record.dl_id:
                    raise UserError("Only the Department Lead can approve this request!")
                record.state = 'hr_approve'
            elif record.state == 'hr_approve':
                record.state = 'approved'
            else:
                raise UserError("Cannot approve at current state!")

    def action_reject(self):
        self.ensure_one()
        current_employee = self.env.user.employee_ids[:1]

        if self.state == 'pm_approve' and current_employee != self.pm_id:
            raise UserError("Only the Project Manager can reject this request!")
        elif self.state == 'dl_approve' and current_employee != self.dl_id:
            raise UserError("Only the Department Lead can reject this request!")
        elif self.state not in['pm_approve', 'dl_approve', 'hr_approve']:
            raise UserError("You cannot reject at this state!")

        return {
            'name': 'Nhập lý do từ chối',
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'