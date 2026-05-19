# Nascente Soluções Contábeis — Sistema de Gestão

## Como executar

### Requisitos
- Python 3.9+ instalado
- Windows 10/11 (ou Linux/macOS)

### Instalação (primeira vez)

```bash
pip install -r requirements.txt
```

### Executar

```bash
python main.py
```

### Login inicial
- **Usuário:** `admin`
- **Senha:** `admin123`
> ⚠️ Altere a senha do administrador após o primeiro acesso.

---

## Gerar executável Windows (.exe)

```bash
pip install pyinstaller
pyinstaller build_windows.spec
```
O executável será gerado em `dist/NascenteGestao/NascenteGestao.exe`

---

## Módulos do sistema

| Módulo | Função |
|--------|--------|
| **Clientes** | Cadastro completo de clientes (PJ/PF), dados, endereço, regime tributário, honorário |
| **Ordens de Serviço** | Emissão de OS com itens, cálculo automático, geração de PDF, linha de assinatura |
| **Contratos** | Contratos personalizados por modalidade, editor de cláusulas, geração de PDF |
| **Comercial / Caixa** | Honorários, fluxo de caixa, lançamento de receitas/despesas, saldo |
| **Documentos** | Pasta por cliente, anexar arquivos, visualizar histórico de OS e contratos |
| **Departamentos** | Cadastro de departamentos do escritório |
| **Usuários** | Gerenciamento de usuários com hierarquia de acesso |

## Hierarquia de acesso

| Perfil | Permissões |
|--------|------------|
| **Administrador** | Acesso total + gerenciar usuários |
| **Gerente** | Tudo exceto usuários + configurações do escritório |
| **Contador** | Clientes, OS, Contratos, Documentos, Caixa |
| **Assistente** | Visualização + operações básicas |

## Configurações do escritório
Vá em **Configurações** (canto inferior do menu) para preencher os dados do escritório que aparecerão nos PDFs gerados.

## Dados armazenados
- Banco de dados: `data/nascente.db`
- Documentos dos clientes: `data/clientes/<id>_<nome>/`
