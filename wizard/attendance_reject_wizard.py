from odoo import fields, models

class AttendanceRejectWizard(models.TransientModel):
    _name = 'attendance.reject.wizard'
    _description = 'Wizard Từ chối đơn quên chấm công'

    request_id = fields.Many2one('attendance.request', string='Đơn yêu cầu', required=True)
    reason = fields.Text(string='Lý do từ chối', required=True)

    def action_confirm_reject(self):
        # Đổi trạng thái đơn gốc
        self.request_id.state = 'rejected'
        # Ghi log vào chatter
        self.request_id.message_post(body=u"Đơn bị từ chối với lý do: %s" % self.reason)