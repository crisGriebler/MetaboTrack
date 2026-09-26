# Implantação inicial no Google Cloud

## Serviço publicado

- **URL:** `https://metabotrack-gjl42kao4q-rj.a.run.app`
- **Projeto:** `metabotrack-509620`
- **Região:** `southamerica-east1` (São Paulo)
- **Plataforma:** Cloud Run
- **Escala:** mínimo de 0 e máximo de 1 instância
- **Memória:** 1 GiB

O endpoint é acessível para iniciar o login Google. O dashboard só é apresentado depois de autenticação OAuth e validação da lista de e-mails autorizados.

## Controle de acesso

O Google OAuth está em modo de testes. As contas autorizadas são:

- `cristiangrb@gmail.com`
- `mariasessak@gmail.com`
- `grieblercrisgcp@gmail.com`

O cliente OAuth e o segredo de sessão ficam no Secret Manager, no segredo `metabotrack-streamlit-auth`. Eles não são versionados nem expostos pelo aplicativo.

## Dados e permissões

| Componente | Configuração |
| --- | --- |
| Firestore Native | Exames de bioimpedância confirmados e metadados, em `southamerica-east1` |
| Cloud Storage | Bucket privado `metabotrack-509620-patient-data`, com acesso uniforme |
| Fotos iniciais | 12 imagens em `patients/maria-helena/photos/`, sem acesso público |
| Artifact Registry | Repositório privado `metabotrack`, em `southamerica-east1` |
| Conta de execução | `metabotrack-run`, com acesso a Firestore, somente ao bucket da aplicação e ao segredo necessário |

A conta de execução não possui papéis administrativos no projeto.

## Validações realizadas

1. O Cloud Build concluiu a imagem `app:43fee81` com sucesso.
2. A revisão do Cloud Run ficou pronta e respondeu à URL publicada.
3. Sem login, a interface apresenta apenas a tela de autenticação, sem dados da paciente.
4. O arquivo estático do Streamlit retornou `200 application/javascript`.
5. O Console confirmou o envio de 12 arquivos JPEG e o status `Not public` para as fotos.

## Operação futura

Para publicar uma nova versão, gere uma nova imagem no Artifact Registry e faça o deploy mantendo as variáveis `METABOTRACK_STORAGE_MODE=gcp`, `METABOTRACK_BUCKET`, `METABOTRACK_PATIENT_ID`, `METABOTRACK_AUTH_ENABLED=true`, a lista de e-mails autorizados e o vínculo com o segredo `metabotrack-streamlit-auth`.

Para revogar uma pessoa, remova o e-mail da lista de usuários de teste no Google Auth Platform e da variável `METABOTRACK_ALLOWED_EMAILS` do Cloud Run.
