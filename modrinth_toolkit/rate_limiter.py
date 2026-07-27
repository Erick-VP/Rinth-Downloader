"""
Rate limiter simples e reutilizável. Garante um intervalo mínimo entre
chamadas e faz backoff exponencial quando a API responde 429 (rate limit)
ou 403 (às vezes usado por CDNs pra bloqueio temporário também).

Pensado pra ser genérico o bastante pra servir tanto o client do Modrinth
(mais tolerante) quanto, no futuro, o da CurseForge (bem mais restritivo) —
só mudar o `min_interval` e o `max_backoff` na hora de instanciar.
"""
import time
import threading

from . import logging_setup

log = logging_setup.get_logger(__name__)


class RateLimiter:
    def __init__(self, min_interval: float = 0.2, max_backoff: float = 900.0):
        """
        min_interval: segundos mínimos entre uma chamada e outra (mesmo sem erro)
        max_backoff: teto em segundos pro backoff exponencial em caso de 429/403
        """
        self.min_interval = min_interval
        self.max_backoff = max_backoff
        self._lock = threading.Lock()
        self._last_call = 0.0
        self._current_backoff = 0.0

    def wait_before_call(self) -> None:
        """Chama essa função antes de cada requisição. Respeita o intervalo mínimo e qualquer backoff ativo."""
        with self._lock:
            now = time.monotonic()
            wait_for = max(
                self.min_interval - (now - self._last_call),
                self._current_backoff,
            )
            if wait_for > 0:
                log.debug(f"Aguardando {wait_for:.1f}s antes da próxima chamada (rate limit).")
                time.sleep(wait_for)
            self._last_call = time.monotonic()
            self._current_backoff = 0.0

    def register_rate_limit_hit(self) -> None:
        """Chama essa função quando a API responder 429/403 por rate limit. Dobra o backoff pra próxima chamada."""
        with self._lock:
            self._current_backoff = min(
                self.max_backoff,
                (self._current_backoff * 2) if self._current_backoff else 5.0,
            )
            log.warning(
                f"Rate limit detectado. Próxima chamada vai esperar "
                f"{self._current_backoff:.0f}s antes de tentar de novo."
            )

    def register_success(self) -> None:
        """Reseta o backoff depois de uma chamada bem-sucedida."""
        with self._lock:
            self._current_backoff = 0.0
