import logging
import time
from contextlib import contextmanager


MARKERS = {
    'info':    '[INF]',
    'ok':      '[OK]',
    'warn':    '[WARN]',
    'err':     '[ERR]',
    'exc':     '[EXC]',
    'in':      '[IN]',
    'out':     '[OUT]',
    'flow':    '[FLOW]',
    'debug':   '[DBG]',
    'timer':   '[TIME]',
}

MAX_VALUE_LEN = 500


def _fmt(**kw):
    if not kw:
        return ''
    pairs = []
    for k, v in kw.items():
        if isinstance(v, str) and len(v) > MAX_VALUE_LEN:
            v = v[:MAX_VALUE_LEN] + '...(truncated)'
        elif isinstance(v, bytes):
            v = repr(v[:MAX_VALUE_LEN])
        pairs.append(f'{k}={v}')
    return ' | ' + ' | '.join(pairs)


class DTBLogger:
    """Centralised DTB logger with visually-scannable ASCII markers.

    Usage in any module file::

        from ..models.dtb_logger import DTBLogger
        log = DTBLogger('TILL')

        log.info('CREATE', id=rec.id, name=rec.name)
        log.ok('RECONCILED', xref=xref, invoice=inv.name)
        log.warn('NO_TILL', reason='no active till found')
        log.err('PAYMENT_FAILED', result_code=code, desc=desc)
        log.exc('VALIDATE_EXCEPTION', error=str(e))

        # Boundaries
        log.incoming('WEBHOOK', endpoint='/callback', xref=xref)
        log.outgoing('STK_PUSH', url=api_url, xref=xref)

        # Flow tracing
        log.flow('C2B_PROCESS', state='done', tx_id=tx.id)

        # Timed block
        with log.timed('HTTP_POST', url=api_url):
            resp = requests.post(api_url, ...)
    """

    def __init__(self, component):
        self.component = component.upper()
        self._logger = logging.getLogger(f'mobipine_odoo_dtb.{component}')

    def _log(self, marker, level, step, **kw):
        msg = '%s [%s] %s%s' % (marker, self.component, step, _fmt(**kw))
        if level == 'info':
            self._logger.info(msg)
        elif level == 'warning':
            self._logger.warning(msg)
        elif level == 'error':
            self._logger.error(msg)
        elif level == 'debug':
            self._logger.debug(msg)

    # ── Public helpers ──────────────────────────────────────────────

    def info(self, step, **kw):
        self._log(MARKERS['info'], 'info', step, **kw)

    def ok(self, step, **kw):
        self._log(MARKERS['ok'], 'info', step, **kw)

    def warn(self, step, **kw):
        self._log(MARKERS['warn'], 'warning', step, **kw)

    def err(self, step, **kw):
        self._log(MARKERS['err'], 'error', step, **kw)

    def exc(self, step, **kw):
        msg = '%s [%s] %s%s' % (MARKERS['exc'], self.component, step, _fmt(**kw))
        self._logger.exception(msg)

    def incoming(self, step, **kw):
        self._log(MARKERS['in'], 'info', step, **kw)

    def outgoing(self, step, **kw):
        self._log(MARKERS['out'], 'info', step, **kw)

    def flow(self, step, **kw):
        self._log(MARKERS['flow'], 'info', step, **kw)

    def debug(self, step, **kw):
        self._log(MARKERS['debug'], 'debug', step, **kw)

    # ── Timing ──────────────────────────────────────────────────────

    @contextmanager
    def timed(self, operation, **ctx):
        start = time.perf_counter()
        try:
            yield
        except Exception:
            elapsed = time.perf_counter() - start
            self.err(operation, ms=f'{elapsed*1000:.1f}', **ctx)
            raise
        elapsed = time.perf_counter() - start
        self.ok(operation, ms=f'{elapsed*1000:.1f}', **ctx)

    def start_timer(self):
        return time.perf_counter()

    def end_timer(self, operation, start, **ctx):
        elapsed = time.perf_counter() - start
        self.ok(operation, ms=f'{elapsed*1000:.1f}', **ctx)
