#!/usr/bin/env python3

import paramiko
import socket
import json
import time
import argparse
import sys
from datetime import datetime
from paramiko.ssh_exception import AuthenticationException, SSHException

DEFAULT_IPS_PATH = "/xxxxxx/xxxxxxx/xxxxxxx/xxxxxxxxx/xxxxxxx/ssh-multi-credential-checker.py/IPs;txt"

DEFAULT_CREDS = [
    ("root", "root"),
    ("admin", "admin"),
    ("kali", "kali"),
]

def ler_ips(caminho):
    with open(caminho, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def tentar_credencial(ip, username, password, port=22, timeout=6, cmd="uname -a && whoami", verbose=True, max_output_chars=5000):
    start = time.time()
    tentativa = {
        "username": username,
        "password": password,
        "acesso": False,
        "motivo": None,
        "detalhes": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tempo_segundos": None
    }

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if verbose:
        print(f"    --> Tentando {username}/{password} em {ip} ...")

    try:
        client.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
            auth_timeout=timeout
        )
        if verbose:
            print(f"    [OK] {ip}: autenticação bem-sucedida com {username}/{password}. Executando comando: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        combined = (out + ("\n=== STDERR ===\n" + err if err else "")).strip()
        if len(combined) > max_output_chars:
            combined = combined[:max_output_chars] + "\n...[TRUNCADO]..."

        tentativa["acesso"] = True
        tentativa["motivo"] = "autenticacao_sucesso"
        tentativa["detalhes"] = combined

        if verbose and out:
            print(f"    [STDOUT]\n{out.rstrip()}")
        if verbose and err:
            print(f"    [STDERR]\n{err.rstrip()}")

    except AuthenticationException:
        tentativa["motivo"] = "autenticacao_falhou"
        tentativa["detalhes"] = "Authentication failed: senha incorreta ou autenticação negada."
        if verbose:
            print(f"    [FALHA] {ip}: autenticação falhou para {username}/{password}.")
    except SSHException as e:
        tentativa["motivo"] = "ssh_exception"
        tentativa["detalhes"] = f"SSHException: {str(e)}"
        if verbose:
            print(f"    [ERRO SSH] {ip}: {e}")
    except socket.timeout:
        tentativa["motivo"] = "timeout"
        tentativa["detalhes"] = "Conexão expirou (timeout)."
        if verbose:
            print(f"    [TIMEOUT] {ip}: conexão expirou.")
    except ConnectionResetError as e:
        tentativa["motivo"] = "connection_reset"
        tentativa["detalhes"] = f"ConnectionResetError: {e}"
        if verbose:
            print(f"    [RESET] {ip}: connection reset by peer.")
    except Exception as e:
        tentativa["motivo"] = "erro_desconhecido"
        tentativa["detalhes"] = f"{type(e).__name__}: {str(e)}"
        if verbose:
            print(f"    [ERRO] {ip}: {type(e).__name__}: {e}")
    finally:
        tentativa["tempo_segundos"] = round(time.time() - start, 3)
        try:
            client.close()
        except Exception:
            pass

    return tentativa

def tentar_ssh_multi_all(ip, creds, port=22, timeout=6, cmd="uname -a && whoami", verbose=True):
    """
    Para um IP, tenta cada credencial (uma vez). Mesmo após sucesso, continua testando os demais.
    Retorna dict com resumo e lista de tentativas.
    """
    resultado = {
        "ip": ip,
        "acesso": False,
        "credenciais_sucesso": [],
        "tentativas": [],
        "timestamp_inicio": datetime.utcnow().isoformat() + "Z",
        "tempo_total_segundos": None
    }
    inicio = time.time()

    for username, password in creds:
        tentativa = tentar_credencial(
            ip=ip,
            username=username,
            password=password,
            port=port,
            timeout=timeout,
            cmd=cmd,
            verbose=verbose
        )
        resultado["tentativas"].append(tentativa)
        if tentativa.get("acesso"):
            resultado["credenciais_sucesso"].append(f"{username}/{password}")

    resultado["acesso"] = len(resultado["credenciais_sucesso"]) > 0
    resultado["tempo_total_segundos"] = round(time.time() - inicio, 3)
    return resultado

def main():
    parser = argparse.ArgumentParser(description="Bruteforce-like SSH checker (testa todas as credenciais por IP). Use com responsabilidade.")
    parser.add_argument("--ips-file", "-f", default=DEFAULT_IPS_PATH, help="Caminho do arquivo com IPs (uma linha por IP).")
    parser.add_argument("--output", "-o", default="resultados_ssh.json", help="Arquivo JSON para salvar os resultados.")
    parser.add_argument("--cmd", "-c", default="uname -a && whoami", help="Comando a rodar no host remoto quando conectar (para trazer 'resultado do terminal').")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar logs verbosos no terminal.")
    parser.add_argument("--port", "-p", type=int, default=22, help="Porta SSH (padrão 22).")
    parser.add_argument("--timeout", "-t", type=int, default=6, help="Timeout de conexão em segundos.")
    parser.add_argument("--creds", "-C", nargs="*", help="Credenciais adicionais user:pass (ex: user1:pass1 user2:pass2).")
    args = parser.parse_args()

    creds = DEFAULT_CREDS.copy()
    if args.creds:
        for item in args.creds:
            if ":" in item:
                user, pwd = item.split(":", 1)
                creds.append((user, pwd))
            else:
                print(f"Ignorando credencial inválida (esperado user:pass): {item}", file=sys.stderr)

    try:
        ips = ler_ips(args.ips_file)
    except FileNotFoundError:
        print(f"Arquivo de IPs não encontrado: {args.ips_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Iniciando varredura de {len(ips)} IP(s). Saída em: {args.output}")
    resultados = []

    try:
        for i, ip in enumerate(ips, start=1):
            print(f"\n[{i}/{len(ips)}] IP: {ip}")
            res = tentar_ssh_multi_all(
                ip=ip,
                creds=creds,
                port=args.port,
                timeout=args.timeout,
                cmd=args.cmd,
                verbose=args.verbose
            )
            resultados.append(res)
            with open(args.output, "w") as out_f:
                json.dump(resultados, out_f, indent=2, ensure_ascii=False)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário. Salvando resultados parciais...")
        with open(args.output, "w") as out_f:
            json.dump(resultados, out_f, indent=2, ensure_ascii=False)
        print(f"Parcial salvo em {args.output}. Saindo.")
        sys.exit(0)

    with open(args.output, "w") as out_f:
        json.dump(resultados, out_f, indent=2, ensure_ascii=False)

    print(f"\nVarredura finalizada. Resultados salvos em {args.output}")

if __name__ == "__main__":
    main()

