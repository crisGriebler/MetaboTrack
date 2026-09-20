import unittest
from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path

from PIL import Image

from metabotrack.bioimpedance import needs_ocr, parse_avabio_380
from metabotrack.photos import list_photos, save_photo


class BioimpedanceParserTests(unittest.TestCase):
    def test_identifies_scanned_pdf(self):
        self.assertTrue(needs_ocr("\n \t"))

    def test_parses_core_avabio_metrics(self):
        text = """
        Peso (kg) 35,1 44,1 53,1 70,7
        Percentual de Gordura 13 18 34,9
        Massa de Gordura (kg) 8 11,1 24,7
        Massa Livre de Gordura (kg) 35 38,1 41,7
        Água Corporal (L) 17,7 24,7 30,6
        IMC 12,3 15,5 24,8
        Taxa Metabólica Basal 1.452 kcal
        Índice Apendicular 6,98 kg/m²
        Idade Metabólica 38 anos
        Nível de Gordura Visceral Nível 11
        """
        result = parse_avabio_380(text)
        self.assertEqual(result["peso_kg"], 70.7)
        self.assertEqual(result["percentual_gordura"], 34.9)
        self.assertEqual(result["massa_gordura_kg"], 24.7)
        self.assertEqual(result["taxa_metabolica_basal_kcal"], 1452.0)
        self.assertEqual(result["gordura_visceral_nivel"], 11.0)

    def test_saves_and_lists_a_progress_photo(self):
        with TemporaryDirectory() as workspace:
            image = Image.new("RGB", (4, 4), "white")
            original = Path(workspace) / "photo.jpg"
            image.save(original)
            saved = save_photo(Path(workspace) / "photos", captured_on=date(2026, 7, 26), direction="frente", original_name="photo.jpg", content=original.read_bytes())
            self.assertTrue(saved.exists())
            self.assertEqual(list_photos(Path(workspace) / "photos")[date(2026, 7, 26)]["frente"], saved)


if __name__ == "__main__":
    unittest.main()
