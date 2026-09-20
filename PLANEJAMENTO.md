# MetaboTrack — proposta de desenvolvimento

Status: proposta para validação. Nenhuma implementação iniciada.

## Objetivo

Criar um aplicativo local em Streamlit para acompanhar inicialmente uma pessoa, reunindo medidas corporais, exames de bioimpedância, fotos e registros do tratamento. Estruturar os dados para uma futura versão com pacientes, médicos e nutricionistas, sem implementar agora toda a operação comercial.

## Escopo inicial proposto

- Perfil da pessoa e data inicial do acompanhamento.
- Cadastro manual e importação de medidas por planilha.
- Upload de exames, extração assistida e conferência antes da confirmação.
- Histórico de bioimpedância e medidas com gráficos e comparação entre datas.
- Fotos por data e posição, com comparação lado a lado.
- Registro opcional de medicamento, dose e unidade, data da aplicação e observações, conforme informado pelo usuário.
- Correção e exclusão de registros, exportação e backup restaurável.

O registro do tratamento documentará o que foi informado; sugestões de dose e interpretação clínica automática ficam fora do escopo inicial. Layout e funcionalidades adicionais serão discutidos após validar o plano e conhecer os dados.

## Etapas e critérios de validação

### 1. Conhecer os dados e fechar o escopo

Examinar amostras dos exames, da tabela atual de medidas e dos formatos de fotos. Identificar equipamentos, campos, unidades, datas e variações de layout. Definir se o diário de aplicações entra na primeira versão.

Entrega: dicionário de dados, formatos inicialmente suportados e lista final das funcionalidades.

Validação: os registros existentes podem ser representados sem perder informações relevantes. Valores não disponíveis permanecem ausentes, nunca zero.

### 2. Base local e cadastro manual

Criar o projeto Python, interface inicial Streamlit e banco SQLite. Separar interface, regras de dados, importadores e armazenamento. Implementar um perfil inicial, medidas manuais e bioimpedância manual para permitir uso mesmo quando a extração falhar.

Cada registro terá identificador da pessoa, data da avaliação e origem. Exames manterão o equipamento e o vínculo com o arquivo original. Arquivos ficarão em pasta de dados própria, com referências no banco.

Validação: cadastrar, consultar e corrigir uma avaliação; fechar e reabrir o aplicativo sem perder os dados.

### 3. Modelo de medidas e importação

Entregar modelo XLSX e alternativa CSV. Uma linha por data de avaliação. Disponibilizar prévia, mensagens por linha, validação de unidades e detecção de possíveis duplicatas antes de salvar. Uma planilha existente poderá receber um mapeamento de colunas após inspeção.

Modelo proposto:

| Campo | Formato/unidade | Obrigatoriedade |
| --- | --- | --- |
| data | DD/MM/AAAA | Obrigatório |
| peso_kg | kg | Opcional |
| cintura_cm | cm | Opcional |
| abdomen_cm | cm | Opcional |
| quadril_cm | cm | Opcional |
| busto_cm | cm | Opcional |
| braco_direito_cm | cm | Opcional |
| braco_esquerdo_cm | cm | Opcional |
| coxa_direita_cm | cm | Opcional |
| coxa_esquerda_cm | cm | Opcional |
| panturrilha_direita_cm | cm | Opcional |
| panturrilha_esquerda_cm | cm | Opcional |
| observacoes | Texto livre | Opcional |

Exigir pelo menos uma medida além da data. A pessoa será selecionada na importação. Campos vazios representam ausência de medição. No CSV, usar UTF-8, separador ponto e vírgula e vírgula decimal. Documentar os locais de medição conforme a prática já utilizada, mantendo cintura e abdômen distintos.

Validação: importar uma amostra e conferir todas as linhas; testar campos vazios, datas inválidas, números com vírgula e reimportação do mesmo arquivo.

### 4. Extração dos exames de bioimpedância

Começar pelo modelo real de exame disponível. PDFs com texto permitem extração direta; digitalizações e fotos precisam de OCR (reconhecimento de texto). Selecionar a ferramenta de OCR depois de avaliar as amostras e a instalação local.

Fluxo: upload → identificação do formato → extração → normalização de nomes/unidades → prévia junto ao original → correções → confirmação → gravação.

Campos candidatos: data, peso, IMC, gordura corporal percentual e em kg, massa muscular esquelética, massa livre de gordura, água corporal, gordura visceral e metabolismo basal, apenas quando presentes e identificáveis no laudo. Massa muscular e massa livre de gordura serão campos distintos. A medida de gordura visceral conservará a unidade ou escala do equipamento.

Guardar origem, valor extraído e valor confirmado. Campos ambíguos ficam pendentes; não estimar valores ausentes. Tratar duplicatas, falhas e layouts desconhecidos sem salvar resultados silenciosamente. Não enviar exames a serviços externos por padrão.

Validação: comparar cada campo extraído com os laudos de referência e verificar que ambiguidades e falhas aparecem para revisão. O suporte inicial será limitado aos modelos efetivamente verificados.

### 5. Métricas e evolução

Criar séries de peso, gordura, massa muscular e medidas disponíveis. Comparar com a primeira avaliação, a anterior ou uma data selecionada. Exibir variação absoluta e relativa quando houver base válida; para percentuais de gordura, apresentar também a diferença em pontos percentuais.

Manter medidas manuais e dados dos exames identificáveis pela origem. Não misturar automaticamente campos de nomes semelhantes ou escalas de equipamentos diferentes. Dados ausentes serão lacunas. Gráficos mostrarão datas reais, unidades e quantidade de avaliações disponível.

Validação: conferir cálculos com exemplos conhecidos, inclusive avaliação única, dados incompletos, base zero e duas fontes na mesma data.

### 6. Fotos e diário do tratamento

Adicionar fotos por data e posição (frente, lado, costas), comparação de duas datas e exclusão. Preservar o original e manter orientação e proporções na exibição. Registrar aplicações e observações se o módulo tiver sido aprovado na etapa 1.

Validação: selecionar duas fotos da mesma posição, conferir datas e testar persistência e exclusão. Para aplicações, conferir dose e unidade exatamente como cadastradas.

### 7. Uso cotidiano e recuperação dos dados

Documentar instalação e inicialização no Windows, exportação, backup e restauração. Verificar que o backup inclui banco e anexos, e testar a restauração em uma pasta separada. Manter dados pessoais, fotos, laudos e banco fora do Git.

O repositório atual está dentro do OneDrive. Definir uma pasta de dados fora do repositório e, se a intenção for armazenamento somente local, fora das pastas sincronizadas. Usar cópia consistente do banco para backup.

Validação: executar o fluxo completo com os dados reais revisados e recuperar um backup sem perder vínculos com exames ou fotos.

## Arquitetura proposta

- Python e Streamlit: interface local.
- SQLite: persistência inicial.
- Pastas locais: exames e fotos; banco guarda referências e metadados.
- Camada de importação independente: planilhas, PDF textual e OCR.
- Camada de métricas independente da interface, para reutilização futura.
- Identificadores de pessoa desde o início; autenticação e compartilhamento ficam para a versão profissional.

## Evolução para uso profissional

Planejar separadamente autenticação, perfis e permissões, vínculo entre profissionais e pacientes, isolamento entre clientes, histórico de alterações, consentimento e gestão dos dados, hospedagem, backups e requisitos de privacidade aplicáveis. Avaliar PostgreSQL e uma API conforme houver necessidade de acesso simultâneo e outras interfaces. Essa evolução exige uma etapa própria antes de disponibilizar a terceiros.

## Sequência de colaboração

Validar primeiro este plano. Depois, examinar amostras e concluir a etapa 1. Discutir a navegação e o layout com os campos reais conhecidos, antes de implementar as telas. Apresentar cada entrega para validação antes de avançar à próxima etapa.

## Referências técnicas consultadas

- Upload no Streamlit: https://docs.streamlit.io/1.48.0/develop/api-reference/widgets/st.file_uploader
- Extração de PDF e limitações para imagens/OCR: https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md
