"""Unit test untuk TokenBudget — core/budget.py."""

from core.budget import TokenBudget


class TestSpend:
    def test_sisa_awal_sesuai_total(self):
        b = TokenBudget(1000)
        assert b.remaining == 1000

    def test_spend_mengurangi_remaining(self):
        b = TokenBudget(1000)
        b.spend(300)
        assert b.remaining == 700

    def test_spend_bertumpuk(self):
        b = TokenBudget(1000)
        b.spend(200)
        b.spend(300)
        b.spend(100)
        assert b.remaining == 400


class TestExhausted:
    def test_belum_exhausted(self):
        b = TokenBudget(100)
        b.spend(50)
        assert not b.exhausted

    def test_exhausted_tepat_sisa_0(self):
        b = TokenBudget(100)
        b.spend(100)
        assert b.exhausted

    def test_exhausted_melebihi(self):
        b = TokenBudget(100)
        b.spend(150)
        assert b.exhausted
        assert b.remaining == 0  # tidak negatif


class TestCritical:
    def test_critical_saatsisa_kurang_30_pct(self):
        b = TokenBudget(100)
        b.spend(75)  # sisa 25 = 25%
        assert b.critical

    def test_tidak_critical_saatsisa_50_pct(self):
        b = TokenBudget(100)
        b.spend(50)  # sisa 50 = 50%
        assert not b.critical

    def test_critical_batas_30_pct(self):
        b = TokenBudget(100)
        b.spend(70)  # sisa 30 = 30%
        assert not b.critical  # 30% belum critical (<30%)

    def test_tidak_critical_jika_sudah_exhausted(self):
        b = TokenBudget(100)
        b.spend(100)
        assert not b.critical  # exhausted bukan critical


class TestPctLeft:
    def test_persen_awal_100(self):
        b = TokenBudget(1000)
        assert b.pct_left == 100.0

    def test_persen_setengah(self):
        b = TokenBudget(1000)
        b.spend(500)
        assert b.pct_left == 50.0

    def test_persen_nol_jika_exhausted(self):
        b = TokenBudget(100)
        b.spend(200)
        assert b.pct_left == 0.0


class TestMeter:
    def test_meter_mengandung_emoji(self):
        b = TokenBudget(1000)
        m = b.meter()
        assert "🟢" in m or "🟡" in m or "🔴" in m

    def test_meter_mengandung_sisa_token(self):
        b = TokenBudget(1000)
        b.spend(300)
        m = b.meter()
        assert "700" in m  # 700/1000

    def test_meter_kritis_emoji_merah(self):
        b = TokenBudget(100)
        b.spend(80)  # sisa 20 = 20% → kritis
        m = b.meter()
        assert "🔴" in m


class TestGuidance:
    def test_normal(self):
        b = TokenBudget(1000)
        g = b.guidance()
        assert "Bekerja normal" in g

    def test_kritis(self):
        b = TokenBudget(100)
        b.spend(80)
        g = b.guidance()
        assert "KRITIS" in g
        assert "Hemat" in g

    def test_habis(self):
        b = TokenBudget(100)
        b.spend(100)
        g = b.guidance()
        assert "HABIS" in g
        assert "done=true" in g
