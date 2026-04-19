from odoo import fields, models


class AttendanceRequestLine(models.Model):
    _name = 'attendance.request.line'
    _description = 'Forgot Attendance Request Line'

    request_id = fields.Many2one(
        'attendance.request',
        string='Tờ đơn gốc',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(string='Ngày quên chấm công', required=True)
    type = fields.Selection(
        [
            ('check_in', 'Check in'),
            ('check_out', 'Check out'),
        ],
        string='Loại',
    )
    reason = fields.Text(string='Lý do', required=True)
