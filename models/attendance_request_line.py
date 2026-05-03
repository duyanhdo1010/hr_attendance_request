import pytz
from odoo import api, exceptions, fields, models

class AttendanceRequestLine(models.Model):
    _name = 'attendance.request.line'
    _description = 'Forgot Attendance Request Line'

    request_id = fields.Many2one('attendance.request', string='Request', required=True, ondelete='cascade')
    
    # 1. KHAI BÁO TRƯỜNG DATE LÀ TRƯỜNG COMPUTE (TỰ ĐỘNG TÍNH)
    date = fields.Date(string='Date', compute='_compute_date', store=True)

    forget_type = fields.Selection([
        ('check_in', 'Check in'),
        ('check_out', 'Check out'),
        ('both', 'Both')
    ], string='Forget type', required=True, default='check_in')

    work_overnight = fields.Boolean(string='Work overnight')

    request_checkin = fields.Datetime(string='Request checkin')
    request_checkout = fields.Datetime(string='Request checkout')
    request_checkout_overnight = fields.Datetime(string='Request checkout overnight')

    actual_checkin = fields.Datetime(string='Actual first checkin (time)')
    actual_checkout = fields.Datetime(string='Actual first checkout (time)')

    reason = fields.Char(string='Reason', required=True)
    evidence = fields.Binary(string='Evidence')
    evidence_name = fields.Char(string='Evidence Name')
    late_approve = fields.Boolean(string='Late approve')

    @api.depends('request_checkin', 'request_checkout', 'actual_checkin', 'actual_checkout')
    def _compute_date(self):
        for line in self:
            source_dt = (
                line.request_checkin or 
                line.request_checkout or 
                line.actual_checkin or 
                line.actual_checkout
            )
            if source_dt:
                user_tz_name = self.env.user.tz or 'UTC'
                user_tz = pytz.timezone(user_tz_name)
                utc_dt = pytz.utc.localize(source_dt)
                local_dt = utc_dt.astimezone(user_tz)
                
                line.date = local_dt.date()
            else:
                line.date = False


    @api.constrains('actual_checkin', 'actual_checkout', 'date')
    def _check_logic_and_duplicate(self):
        for line in self:
            if line.actual_checkin and line.actual_checkout:
                if line.actual_checkout <= line.actual_checkin:
                    raise exceptions.ValidationError("Logic error: Check-out time must be later than Check-in time!")

            if line.date and line.request_id.employee_id:
                domain =[
                    ('date', '=', line.date),
                    ('request_id.employee_id', '=', line.request_id.employee_id.id),
                    ('id', '!=', line.id),
                    ('request_id.state', '!=', 'rejected')
                ]
                
                if self.env['attendance.request.line'].search_count(domain) > 0:
                    formatted_date = line.date.strftime('%d/%m/%Y')
                    raise exceptions.ValidationError(
                        "A forgotten attendance request for %s already exists. Please review previous requests." % formatted_date
                    )