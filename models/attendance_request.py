from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import UserError
from datetime import timedelta

class AttendanceRequest(models.Model):
    _name = 'attendance.request'
    _description = 'Forgot Attendance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', copy=False)
    name = fields.Char(string='Request Code', default='New', copy=False)
    
    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee', 
        required=True,
        default=lambda self: self.env.user.employee_ids[:1]
    )
    request_date = fields.Date(string='Created Date', default=fields.Date.context_today)
    deadline_date = fields.Date(string='Approval Deadline', track_visibility='onchange')
    pm_id = fields.Many2one('hr.employee', string='Direct Manager', required=True)
    dl_id = fields.Many2one('hr.employee', string='Department Lead', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pm_approve', 'Waiting for PM Approval'),
        ('dl_approve', 'Waiting for DL Approval'),
        ('hr_approve', 'Waiting for HR Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', track_visibility='onchange')
    
    line_ids = fields.One2many('attendance.request.line', 'request_id', string='Details')

    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department_id', store=True)

    note = fields.Text("Note")
    commit_checkbox = fields.Boolean(string="I commit that the provided information is accurate")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('attendance.request') or 'New'
        return super(AttendanceRequest, self).create(vals)    

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
            record.deadline_date = fields.Date.context_today(record) + timedelta(days=2)

            msg = u"I have just submitted a forgotten attendance request. Please review and approve it."
            record._send_notification(record.pm_id, msg)

    def action_approve(self):
        current_employee = self.env.user.employee_ids[:1]
        is_admin = self.env.uid == SUPERUSER_ID or self.env.user.has_group('base.group_erp_manager')
        for record in self:
            if record.state == 'pm_approve':
                if current_employee != record.pm_id and not is_admin:
                    raise UserError("Only the Project Manager can approve this request!")
                record.state = 'dl_approve'
                msg = u"The PM has approved %s's request. Please continue with DL approval." % record.employee_id.name
                record._send_notification(record.dl_id, msg)
            elif record.state == 'dl_approve':
                if current_employee != record.dl_id and not is_admin:
                    raise UserError("Only the Department Lead can approve this request!")
                record.state = 'hr_approve'
                msg = u"The DL has approved the request. It is now waiting for HR approval."
                record._send_notification(record.employee_id, msg)
            elif record.state == 'hr_approve':
                record.state = 'approved'
                msg = u"Your forgotten attendance request has been fully approved."
                record._send_notification(record.employee_id, msg)
            else:
                raise UserError("Cannot approve at current state!")

    def action_reject(self):
        self.ensure_one()
        current_employee = self.env.user.employee_ids[:1]
        is_admin = self.env.uid == SUPERUSER_ID or self.env.user.has_group('base.group_erp_manager')

        if self.state == 'pm_approve' and current_employee != self.pm_id and not is_admin:
            raise UserError("Only the Project Manager can reject this request!")
        elif self.state == 'dl_approve' and current_employee != self.dl_id and not is_admin:
            raise UserError("Only the Department Lead can reject this request!")
        elif self.state not in['pm_approve', 'dl_approve', 'hr_approve']:
            raise UserError("You cannot reject at this state!")

        return {
            'name': 'Enter Rejection Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'
    
    def _send_notification(self, employee_to_notify, message):
        for record in self:
            if employee_to_notify and employee_to_notify.user_id and employee_to_notify.user_id.partner_id:
                partner_id = employee_to_notify.user_id.partner_id.id
                record.message_post(
                    body=message,
                    partner_ids=[partner_id],
                    subtype='mail.mt_comment'
                )