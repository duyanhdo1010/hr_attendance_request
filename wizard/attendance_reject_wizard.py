from odoo import fields, models

class AttendanceRejectWizard(models.TransientModel):
    _name = 'attendance.reject.wizard'
    _description = 'Forgot Attendance Request Reject Wizard'

    request_id = fields.Many2one('attendance.request', string='Request', required=True)
    reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        for wizard in self:
            wizard.request_id.state = 'rejected'
            message = u"Your request has been rejected for the following reason: %s" % wizard.reason
            wizard.request_id._send_notification(wizard.request_id.employee_id, message)
        return {'type': 'ir.actions.act_window_close'}