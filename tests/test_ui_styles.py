from pathlib import Path
import unittest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class ProgressCardStyleTests(unittest.TestCase):
    def test_progress_card_uses_dark_text_on_a_light_surface(self) -> None:
        """Keep the dashboard cards readable when Streamlit selects its light theme."""
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn(".progress-card { background: #ffffff;", app_source)
        self.assertIn(".progress-title { color: #1f2937 !important;", app_source)
        self.assertIn(".progress-values span { display: block; color: #4b5563 !important;", app_source)
        self.assertIn(".progress-values strong { display: block; color: #111827 !important;", app_source)
        self.assertIn(".progress-variation { color: #374151 !important;", app_source)


if __name__ == "__main__":
    unittest.main()
