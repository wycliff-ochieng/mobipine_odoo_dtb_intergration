import json
import logging
from odoo import http
from odoo.http import request
from ..models.dtb_logger import DTBLogger

_logger = logging.getLogger(__name__)
log = DTBLogger('CONTROLLER')


class DtbMojaController(http.Controller):

    @http.route([
        '/api/dtb/validate-reference',
        '/api/dtb/validate-reference/<string:till_number>/<path:reference_number>/<string:amount>'
    ], type='http', auth='none', methods=['GET'], csrf=False)
    def validate_reference(self, till_number=None, reference_number=None, amount=None, **kwargs):
        # --- HEADER LOGGING ---
        try:
            _logger.info('[DTB][HEADERS] validate_reference | Incoming Headers:\n%s',
                         json.dumps(dict(request.httprequest.headers.items()), indent=4))
        except Exception as e:
            _logger.error('[DTB][HEADERS] Failed to log headers: %s', str(e))
        # ----------------------

        api_key = request.httprequest.headers.get('Authorization', '')
        masked_key = api_key[:15] + '...' if api_key and len(api_key) > 15 else api_key

        log.incoming('validate_reference | ENTER',
                     till_number=till_number, ref=reference_number, amount=amount,
                     kwargs=kwargs, auth=masked_key)

        try:
            # --- AUTHORIZATION GUARD REMOVED FOR UAT TESTING ---
            # if not self._is_authorized(api_key):
            #     log.warn('validate_reference | UNAUTHORIZED', key=masked_key)
            #     return request.make_response(
            #         json.dumps({'error': 'Unauthorized'}),
            #         headers=[('Content-Type', 'application/json')],
            #         status=401,
            #     )

            till_number = till_number or kwargs.get('tillNumber')
            reference = reference_number or kwargs.get('referenceNumber')
            amount = amount or kwargs.get('transactionAmount', '0')

            log.info('validate_reference | PARAMS',
                     till=till_number, ref=reference, amount=amount)

            if not till_number or not reference:
                log.warn('validate_reference | MISSING_PARAMS',
                         till=till_number, ref=reference)
                return request.make_response(
                    json.dumps({'error': 'Missing required parameters'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400,
                )

            result = request.env['dtb.moja.validation'].with_user(http.request.env.user).sudo()._validate_reference(
                till_number, reference, amount
            )
            log.info('validate_reference | RESULT', found=result is not None)

            if result is None:
                return request.make_response(
                    json.dumps({'error': 'Reference not found or amount mismatch'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404,
                )

            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')],
                status=200,
            )

        except Exception:
            log.exc('validate_reference | EXCEPTION')
            return request.make_response(
                json.dumps({'error': 'Internal server error'}),
                headers=[('Content-Type', 'application/json')],
                status=500,
            )

    @http.route('/api/dtb/callback/notification', type='http', auth='none',
                methods=['POST'], csrf=False)
    def payment_callback(self):
        # -- HEADER LOGGING
        try:
            _logger.info('[DTB][HEADERS] payment_callback | Incoming Headers:\n%s',
                         json.dumps(dict(request.httprequest.headers.items()), indent=4))
            _logger.info('[DTB][BODY] payment_callback | Raw Body:\n%s',
                         request.httprequest.data.decode('utf-8', errors='replace'))
        except Exception as e:
            _logger.error('[DTB][HEADERS] Failed to log headers/body: %s', str(e))
        #

        try:
            payload = json.loads(request.httprequest.data)
        except Exception:
            payload = {}
        log.incoming('payment_callback | ENTER', payload=str(payload)[:500])
        try:
            result = request.env['dtb.moja.validation'].with_user(http.request.env.user).sudo()._process_callback_payload(payload)
            log.ok('payment_callback | RESULT', result=result)
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')],
            )
        except Exception:
            log.exc('payment_callback | EXCEPTION')
            return request.make_response(
                json.dumps({'ack_code': '99', 'ack_description': 'INTERNAL_ERROR'}),
                headers=[('Content-Type', 'application/json')],
            )

    @http.route('/api/dtb/stk-callback', type='http', auth='none',
                methods=['POST'], csrf=False)
    def stk_callback(self):
        # --- HEADER LOGGING ---
        try:
            _logger.info('[DTB][HEADERS] stk_callback | Incoming Headers:\n%s',
                         json.dumps(dict(request.httprequest.headers.items()), indent=4))
            _logger.info('[DTB][BODY] stk_callback | Raw Body:\n%s',
                         request.httprequest.data.decode('utf-8', errors='replace'))
        except Exception as e:
            _logger.error('[DTB][HEADERS] Failed to log headers/body: %s', str(e))
        # ----------------------

        try:
            payload = json.loads(request.httprequest.data)
        except Exception:
            payload = {}
        log.incoming('stk_callback | ENTER', payload=str(payload)[:500])
        try:
            result = request.env['dtb.moja.validation'].with_user(http.request.env.user).sudo()._process_stk_callback(payload)
            log.ok('stk_callback | RESULT', result=result)
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')],
            )
        except Exception:
            log.exc('stk_callback | EXCEPTION')
            return request.make_response(
                json.dumps({'ack_code': '99', 'ack_description': 'INTERNAL_ERROR'}),
                headers=[('Content-Type', 'application/json')],
            )

    def _is_authorized(self, api_key):
        if not api_key:
            log.warn('_is_authorized | NO_KEY')
            return False
        bearer = api_key.replace('Bearer ', '')
        found = request.env['dtb.moja.till'].sudo().search([
            ('api_key', '=', bearer),
        ], limit=1)stock
        log.info('_is_authorized | SEARCH',
                 key_prefix=bearer[:8], found=bool(found))
        return bool(found)
