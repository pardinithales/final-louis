# Deploy Backend FastAPI com Docker + Traefik

## 1. Pré-requisitos
- Docker e Docker Compose instalados na VPS
- Domínio apontando para o IP da VPS

## 2. Estrutura de arquivos
```
backend/
  app/
  Dockerfile
  docker-compose.yml
  traefik/
    traefik.yml
    acme.json
  .env
```

## 3. Configuração Traefik
- Edite `docker-compose.yml` e `traefik/traefik.yml` com seu domínio e e-mail.
- Crie arquivo vazio para certificados:
  ```sh
  mkdir -p traefik
  touch traefik/acme.json
  chmod 600 traefik/acme.json
  ```

## 4. Deploy
- Copie todos os arquivos para a VPS (ex: `scp -r backend/ usuario@ip_vps:/caminho/`)
- Acesse a pasta `backend` na VPS
- Crie/edite `.env` conforme `.env.example`
- Rode:
  ```sh
  docker compose up -d
  ```
- Acesse https://seu_dominio/
- Dashboard Traefik: https://seu_dominio:8080 (opcional, liberar porta 8080 se desejar)

## 5. Dicas de Troubleshooting
- Logs backend: `docker compose logs backend`
- Logs traefik: `docker compose logs traefik`
- Certifique-se que as portas 80 e 443 estão liberadas no firewall

---
Dúvidas ou problemas? Só avisar!
