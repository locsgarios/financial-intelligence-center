import os
import requests
from typing import Optional


BASE_URL = "https://brapi.dev/api"


class BrapiClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("BRAPI_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "financial-agents/1.0"})

    def _get(self, path: str, params: dict = None) -> dict:
        params = params or {}
        if self.token:
            params["token"] = self.token
        response = self.session.get(f"{BASE_URL}{path}", params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_quote(self, tickers: list[str]) -> list[dict]:
        """Cotação atual de uma ou mais ações (uma por vez para plano free)."""
        results = []
        for ticker in tickers:
            try:
                try:
                    data = self._get(f"/quote/{ticker}", {"fundamental": "true", "dividends": "true"})
                except Exception:
                    data = self._get(f"/quote/{ticker}")
                results.extend(data.get("results", []))
            except Exception as e:
                print(f"Aviso: falha ao buscar {ticker}: {e}")
        return results

    def get_fundamentals(self, ticker: str) -> dict:
        """Dados fundamentalistas de uma ação."""
        results = self.get_quote([ticker])
        return results[0] if results else {}

    def get_ticker_list(self, limit: int = 500) -> list[str]:
        """Retorna lista de tickers disponíveis na B3."""
        try:
            data = self._get("/quote/list", {"limit": limit, "type": "stock"})
            stocks = data.get("stocks", [])
            return [s["stock"] for s in stocks if s.get("stock")]
        except Exception:
            return []

    def get_single_quote(self, ticker: str) -> dict | None:
        """Cotação de um único ticker, silenciosa em caso de erro."""
        try:
            data = self._get(f"/quote/{ticker}", {"fundamental": "true"})
            results = data.get("results", [])
            return results[0] if results else None
        except Exception:
            try:
                data = self._get(f"/quote/{ticker}")
                results = data.get("results", [])
                return results[0] if results else None
            except Exception:
                return None

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Busca ações pelo nome ou ticker."""
        data = self._get("/quote/list", {"search": query, "limit": limit})
        return data.get("stocks", [])

    def get_inflation(self) -> dict:
        """Retorna dados de inflação (IPCA, IGP-M)."""
        try:
            data = self._get("/v2/inflation", {"country": "brazil"})
            return data.get("results", [])
        except Exception:
            return []

    def get_prime_rate(self) -> list[dict]:
        """Retorna taxa Selic."""
        try:
            data = self._get("/v2/prime-rate", {"country": "brazil"})
            return data.get("results", [])
        except Exception:
            return []
