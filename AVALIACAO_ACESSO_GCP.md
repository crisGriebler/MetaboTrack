# Avaliação de acesso ao GCP

## Projeto alvo

- **ID:** `metabotrack-509620`
- **Região de implantação planejada:** `southamerica-east1` (São Paulo)
- **Data da verificação:** 25/09/2026

## Resultado da verificação

| Item | Situação | Evidência |
| --- | --- | --- |
| Google Cloud CLI local | Não disponível | O comando `gcloud` não está instalado ou não está no `PATH`. |
| Console do Google Cloud | Acesso confirmado | Painel principal do projeto carregado com sucesso. |
| Existência do projeto | Confirmada | Projeto **MetaboTrack**, ID `metabotrack-509620`, número `100093952020`. |
| Conta de faturamento | Ativa | Estimativa apresentada pelo Console: `R$ 0,00` no período atual. |
| APIs habilitadas | Parcialmente confirmadas | O painel de APIs carregou; a lista detalhada será consultada antes do provisionamento. |
| Papéis IAM atuais | Suficientes para implantação inicial | A conta administradora possui `roles/owner`, além dos papéis de leitura exibidos no Console. |

Nenhum recurso foi criado, editado ou cobrado durante esta avaliação.

### Correção do bloqueio inicial

O primeiro teste usava outra conta Google no Chrome e retornou **“Você precisa de acesso adicional”** para a permissão:

```text
resourcemanager.projects.get
```

Após selecionar a conta administradora correta, o Console carregou normalmente. Não há, até este ponto, evidência de política IAM Deny ou Principal Access Boundary bloqueando o projeto.

## Permissões mínimas para uma auditoria de leitura

Conceder temporariamente à conta autenticada, no projeto ou na conta de faturamento conforme indicado:

| Finalidade da auditoria | Papel sugerido | Escopo |
| --- | --- | --- |
| Abrir e identificar o projeto | `roles/resourcemanager.projectViewer` | Projeto `metabotrack-509620` |
| Listar APIs habilitadas | `roles/serviceusage.serviceUsageViewer` | Projeto |
| Ler política IAM e papéis atribuídos | `roles/iam.securityReviewer` | Projeto |
| Ler recursos sem alterar configuração | `roles/viewer` | Projeto |
| Ler conta e vínculo de faturamento | `roles/billing.viewer` | Conta de faturamento |

Os papéis acima são apenas para diagnóstico e não autorizam criação, alteração ou remoção de recursos. Depois da auditoria, eles podem ser mantidos ou removidos conforme a necessidade da conta administradora.

## Permissões para a pessoa que fará o primeiro provisionamento

Estas permissões podem ser temporárias durante a implantação inicial. Depois, o acesso deve ser reduzido ao mínimo necessário.

| Objetivo | Papel IAM recomendado | Escopo |
| --- | --- | --- |
| Consultar projeto e APIs | `roles/viewer` e `roles/serviceusage.serviceUsageViewer` | Projeto |
| Habilitar APIs | `roles/serviceusage.serviceUsageAdmin` | Projeto |
| Criar e atualizar serviço Cloud Run | `roles/run.admin` | Projeto ou serviço |
| Vincular a conta de serviço ao Cloud Run | `roles/iam.serviceAccountUser` | Conta de serviço do runtime |
| Criar a conta de serviço do runtime | `roles/iam.serviceAccountAdmin` | Projeto, temporário |
| Construir e publicar imagem | `roles/cloudbuild.builds.editor` e `roles/artifactregistry.writer` | Projeto e repositório Artifact Registry |
| Criar bucket e configurar acesso uniforme | `roles/storage.admin` | Bucket, temporário |
| Criar Firestore Native | `roles/datastore.owner` | Projeto, temporário |
| Criar e administrar segredos | `roles/secretmanager.admin` | Segredos, temporário |
| Configurar Identity Platform | `roles/identitytoolkit.admin` | Projeto |
| Configurar orçamento e alertas | `roles/billing.costsManager` | Conta de faturamento |
| Vincular ou consultar cobrança do projeto | `roles/billing.projectManager` ou `roles/billing.viewer` | Projeto ou conta de faturamento |

## Permissões da conta de serviço do Cloud Run

A conta de serviço `metabotrack-run` não deve receber `Owner`, `Editor` nem papéis amplos no projeto.

| Recurso | Papel mínimo | Escopo |
| --- | --- | --- |
| Firestore | `roles/datastore.user` | Projeto ou banco da aplicação |
| Bucket privado com fotos e PDFs | `roles/storage.objectAdmin` | Somente o bucket `metabotrack-...` |
| Segredo de configuração de autenticação | `roles/secretmanager.secretAccessor` | Somente o segredo necessário |

O acesso administrativo ao Cloud Run, ao bucket, ao Firestore e aos segredos deve permanecer com a conta administradora, não com a conta de serviço que executa o aplicativo.

## APIs a confirmar ou habilitar

1. Cloud Run Admin API
2. Cloud Build API
3. Artifact Registry API
4. Cloud Firestore API
5. Cloud Storage API
6. Secret Manager API
7. Identity Toolkit API
8. Cloud Resource Manager API
9. Cloud Billing Budget API

## Próximas verificações antes do provisionamento

1. Listar as APIs já habilitadas.
2. Identificar recursos existentes que possam gerar colisão de nomes: serviço Cloud Run, bucket, banco Firestore, repositório Artifact Registry, segredos e contas de serviço.
3. Antes da criação, validar os custos e as regiões dos recursos planejados.

## Referências

- [Papéis IAM do Cloud Run](https://cloud.google.com/run/docs/reference/iam/roles)
- [Papéis do Cloud Storage](https://cloud.google.com/storage/docs/access-control/iam-roles)
- [Papéis do Firestore](https://cloud.google.com/iam/docs/roles-permissions/datastore)
- [Papéis do Secret Manager](https://cloud.google.com/secret-manager/docs/access-control)
- [Papéis da Identity Platform](https://cloud.google.com/identity-platform/docs/access-control)
