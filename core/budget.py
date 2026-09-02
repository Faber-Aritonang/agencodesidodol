"""Token Budget Controller — Dodol sadar kuota & berperilaku adaptif."""


class TokenBudget:
    def __init__(self, total: int = 30000):
        self.total = total
        self.used = 0

    def spend(self, tokens: int):
        self.used += tokens

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.used)

    @property
    def pct_left(self) -> float:
        return self.remaining / self.total * 100 if self.total else 0.0

    @property
    def exhausted(self) -> bool:
        return self.remaining <= 0

    @property
    def critical(self) -> bool:
        """Budget menipis (<30%) — saatnya strategi hemat."""
        return not self.exhausted and self.pct_left < 30

    def meter(self) -> str:
        bar_len = 20
        filled = round(bar_len * self.remaining / self.total)
        bar = "█" * filled + "░" * (bar_len - filled)
        emoji = "🟢" if self.pct_left > 50 else "🟡" if not self.critical else "🔴"
        return f"{emoji} [{bar}] {self.remaining}/{self.total} tok sisa ({self.pct_left:.0f}%)"

    def guidance(self) -> str:
        """Instruksi dinamis untuk LLM berdasarkan kondisi budget."""
        if self.exhausted:
            return "BUDGET HABIS. Segera set done=true dengan ringkasan capaian."
        if self.critical:
            return (f"BUDGET KRITIS ({self.remaining} tok sisa). "
                    "Hemat: hindari eksplorasi, langsung langkah penyelesaian. "
                    "Jika belum selesai sempurna, laporkan progres yang ada.")
        return f"💰 Budget tersisa {self.remaining} token. Bekerja normal."
