# MetaboTrack

Dashboard local em Streamlit para acompanhar a evolução de tratamento com canetas emagrecedoras. A primeira versão acompanha uma paciente e foi estruturada para, futuramente, suportar pacientes, médicos e nutricionistas.

## Visão do dashboard

A barra lateral identifica a paciente e resume os registros disponíveis: avaliações de medidas, exames de bioimpedância e sessões de fotos.

O conteúdo principal apresenta:

- **Evolução desde o início:** peso, cintura/abdômen, gordura corporal e gordura visceral. Cada cartão exibe o valor inicial, o valor atual e a variação entre os dois períodos.
- **Gráfico de bioimpedância:** evolução no tempo dos indicadores escolhidos, incluindo peso, percentual e massa de gordura, massa livre de gordura, IMC e gordura visceral.
- **Gráfico de medidas corporais:** evolução de peso, cintura/abdômen, quadril, busto, coxas e braços conforme a seleção feita no dashboard.
- **Detalhes do último exame:** massa de gordura, massa livre de gordura, IMC e água corporal, novamente com valores inicial, atual e variação.
- **Comparação de fotos:** seleção de duas datas e navegação por Frente, Lado direito, Lado esquerdo e Costas. A avaliação mais antiga é sempre mostrada à esquerda.

## Dados iniciais incluídos

O projeto registra o histórico inicial de duas bioimpedâncias revisadas, de **24/07/2026** e **18/09/2026**, além das medidas corporais de **26/07/2026**, **21/08/2026** e **18/09/2026**. O peso de 21/08 está registrado como **76,0 kg**.

As fotos são armazenadas localmente por data e direção, e não entram no versionamento Git.

## Adicionar um novo exame de bioimpedância

1. Abra **Adicionar novo exame de bioimpedância**.
2. Envie o PDF do laudo.
3. O sistema tenta ler a camada de texto do arquivo; quando ela não está disponível, tenta OCR local.
4. Confira e corrija os valores na tabela de revisão.
5. Marque a confirmação e salve o novo exame.

Nenhum valor extraído automaticamente é salvo sem conferência humana. PDFs digitalizados exigem Tesseract OCR e Poppler instalados e acessíveis pelo `PATH`; sem eles, o formulário permite revisão manual.

## Adicionar novas fotos

1. Abra **Adicionar nova foto** na área de comparação.
2. Informe a data e a direção da imagem.
3. Envie uma foto em JPG, JPEG, PNG ou WEBP.

As fotos passam por validação básica antes de serem salvas na pasta local `data/photos`.

## Estrutura do projeto

```text
app.py                         # Interface Streamlit e composição do dashboard
src/metabotrack/history.py     # Perfil, medidas e histórico inicial
src/metabotrack/bioimpedance.py# Extração, OCR, revisão e SQLite
src/metabotrack/photos.py      # Armazenamento e comparação das fotos
tests/                         # Testes da extração e das fotos
data/                          # Base SQLite, PDFs e fotos locais (ignorado pelo Git)
```

## Executar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Testes

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
