Ferramenta simples em Python para testar múltiplas credenciais SSH em diversos hosts.
O script tenta combinações de usuário/senha em cada IP, registra erros, sucessos, motivos de falha e salva tudo em um arquivo JSON.

Feito para uso em ambiente Linux, com execução em ambiente virtual (venv) e dependência do paramiko. Use somente em máquinas em que você tem permissão.

# SSH Credential Tester

Ferramenta em Python para testar múltiplas credenciais SSH contra uma lista de hosts, registrando **sucessos**, **falhas**, **motivos** e **saídas de comandos**.

> ⚠️ **Aviso legal:** use esta ferramenta apenas em sistemas nos quais você tem autorização para testar.

---

## ✨ Recursos

- Testa várias credenciais por IP  
- Continua tentando credenciais mesmo após um sucesso  
- Executa comando remoto em caso de acesso  
- Salva tudo em um JSON organizado  
- Mostra logs verbosos opcionais (`--verbose`)  
- Salva progresso automaticamente ao interromper (`Ctrl+C`)  
- Aceita credenciais adicionais via CLI  
- Feito para Linux + ambiente virtual (venv)

---

## 📁 Estrutura recomendada

- `ssh-multi-credential-checker.py`
- `IPs.txt`
- `resultados_ssh.json # gerado automaticamente`
- `README.md`
- `venv/ # ambiente virtual`

## 🔧 Instalação (Linux)

### 1) Criar ambiente virtual

`python3 -m venv venv`

2) Ativar o venv
`source venv/bin/activate`

4) (Opcional) Atualizar pip
`python -m pip install --upgrade pip`

6) Instalar dependência (Paramiko)
`pip install paramiko`

▶️ Como executar

Execução padrão:

`python ssh-multi-credential-checker.py --verbose`


Usar outro arquivo de IPs:
```xml
python ssh-multi-credential-checker.py  --ips-file IPs.txt --verbose
```

Escolher outro arquivo de saída:
```xml
python ssh-multi-credential-checker.py --output resultados.json --verbose
```

Adicionar credenciais extras (user:senha):
```xml
python ssh-multi-credential-checker.py --creds admin:123 root:root teste:teste --verbose
```

Executar como root (mantendo venv):
```xml
sudo venv/bin/ssh-multi-credential-checker.py --verbose
```
---

## 📦 Formato do JSON produzido
```xml
{
  "ip": "192.168.1.10",
  "acesso": true,
  "credenciais_sucesso": ["root/root"],
  "tentativas": [
    {
      "username": "root",
      "password": "root",
      "acesso": true,
      "detalhes": "resultado do comando remoto",
      "tempo_segundos": 0.52
    }
  ]
}
```

## ⏹ Interromper com segurança

Para parar:

```xml
Ctrl + C
```
O script salva automaticamente os resultados parciais no arquivo escolhido por --output.

---

## 🔍 Visualizar JSON (formatado)
Via Python:
```xml
python -m json.tool resultados_ssh.json | less -R
```

Via jq:
```xml
jq '.' resultados_ssh.json | less -R
```

---

## 🛠 Problemas comuns
❌ ModuleNotFoundError: No module named 'paramiko'

Ative o venv antes de instalar/rodar:
```xml
source venv/bin/activate
pip install paramiko
```

❌ Authentication failed

Credencial incorreta — o script registra isso no JSON.

❌ SSHException ou Connection reset

O servidor rejeitou/fechou a conexão.

## ✔️ Conclusão

Ferramenta simples e eficaz para auditoria de credenciais SSH.
