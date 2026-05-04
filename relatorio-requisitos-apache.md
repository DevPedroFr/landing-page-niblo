# Relatorio de Requisicao para Infraestrutura Apache

## Objetivo

Garantir que o ambiente Apache dos dominios `niblo.com.br`, `niblo.cloud` e `www.niblo.cloud` aplique corretamente as diretivas de seguranca definidas no projeto e elimine os achados do scan relacionados a headers HTTP, listagem de diretorio e exposicao de banner do servidor.

## Escopo

O projeto ja contem configuracao aplicacional em `.htaccess` para:

- `Content-Security-Policy`
- `X-Frame-Options`
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`
- bloqueio de listagem de diretorio com `Options -Indexes`
- paginas customizadas `403` e `404`
- `Cache-Control` por tipo de arquivo

Para que isso funcione em producao, o Apache precisa aceitar e aplicar essas diretivas.

## Acao Necessaria no Apache

### 1. Permitir leitura do `.htaccess`

No `VirtualHost` ou no bloco `Directory` do `DocumentRoot`, garantir:

```apache
<Directory /caminho/do/site/landing-page-niblo>
    AllowOverride All
    Require all granted
</Directory>
```

Sem `AllowOverride All`, o Apache ignora o `.htaccess` e o scan continuara reportando ausencia de CSP, HSTS, `X-Frame-Options` e `X-Content-Type-Options`.

### 2. Habilitar modulos obrigatorios

Garantir que os modulos abaixo estejam ativos:

- `headers`
- `rewrite` caso o ambiente ja use regras de reescrita

Em distribuicoes Debian/Ubuntu, executar:

```bash
sudo a2enmod headers
sudo a2enmod rewrite
sudo systemctl reload apache2
```

Sem `mod_headers`, os headers configurados no `.htaccess` nao sao enviados nas respostas.

### 3. Reduzir exposicao de versao do Apache

Configurar globalmente no Apache:

```apache
ServerTokens Prod
ServerSignature Off
```

Observacao:

- `ServerSignature Off` ja foi definido no `.htaccess`, ajudando nas paginas de erro servidas pela aplicacao.
- `ServerTokens Prod` precisa ser definido no config global do Apache ou no `apache2.conf` equivalente. Nao deve ser tratado apenas no codigo do projeto.

### 4. Garantir HTTPS efetivo em todos os hosts publicados

O header HSTS so tem efeito em respostas HTTPS validas. Confirmar que:

- `https://niblo.com.br`
- `https://niblo.cloud`
- `https://www.niblo.cloud`

estejam servindo com certificado valido e sem fallback incorreto para HTTP.

### 5. Garantir aplicacao do `.htaccess` no host correto

Validar se o `DocumentRoot` do `VirtualHost` publicado aponta para a pasta do projeto correta e nao para um nivel acima. O arquivo `.htaccess` precisa estar no mesmo escopo efetivo do conteudo servido.

## Exemplo de VirtualHost recomendado

```apache
<VirtualHost *:80>
    ServerName niblo.cloud
    ServerAlias www.niblo.cloud niblo.com.br www.niblo.com.br
    DocumentRoot /var/www/landing-page-niblo

    <Directory /var/www/landing-page-niblo>
        AllowOverride All
        Require all granted
    </Directory>

    RewriteEngine On
    RewriteCond %{HTTPS} !=on
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName niblo.cloud
    ServerAlias www.niblo.cloud niblo.com.br www.niblo.com.br
    DocumentRoot /var/www/landing-page-niblo

    <Directory /var/www/landing-page-niblo>
        AllowOverride All
        Require all granted
    </Directory>

    SSLEngine on
    SSLCertificateFile /caminho/do/certificado/fullchain.pem
    SSLCertificateKeyFile /caminho/do/certificado/privkey.pem
</VirtualHost>
</IfModule>
```

## Validacoes que a Infra precisa executar

### Validar sintaxe do Apache

Debian/Ubuntu:

```bash
sudo apache2ctl configtest
```

RHEL/CentOS:

```bash
sudo httpd -t
```

### Recarregar servico

Debian/Ubuntu:

```bash
sudo systemctl reload apache2
```

RHEL/CentOS:

```bash
sudo systemctl reload httpd
```

### Confirmar headers publicados

Executar:

```bash
curl -I https://niblo.cloud
curl -I https://www.niblo.cloud
curl -I https://niblo.com.br
```

Esperado nas respostas:

- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Confirmar listagem de diretorio bloqueada

Ao acessar diretórios sem arquivo indice, o retorno esperado deve ser `403` ou redirecionamento controlado, nunca listagem de arquivos.

### Confirmar banner reduzido

Em respostas de erro, o servidor nao deve expor algo como `Apache/2.4.58 (Ubuntu)`.

## Achados do scan e origem da correcao

### Resolvidos no projeto, dependentes de aplicacao do Apache

- Ausencia de `Content-Security-Policy`
- Ausencia de protecao anti-clickjacking
- Ausencia de `Strict-Transport-Security`
- Ausencia de `X-Content-Type-Options`
- Revisao de `Cache-Control`
- Navegacao em diretorio habilitada

### Dependente de configuracao global do servidor

- Vazamento de banner de versao do servidor

### Informativos

- deteccao de Cloudflare
- deteccao de HTTP/3

Esses dois ultimos sao informativos e nao exigem correcao no codigo da aplicacao.

## Risco de nao implementacao

Se a infraestrutura nao habilitar `AllowOverride All`, `mod_headers` e `ServerTokens Prod`, os scans continuarao acusando vulnerabilidades mesmo com o projeto corrigido.

## Solicitacao final para a equipe de Infra

Solicita-se:

1. habilitar leitura do `.htaccess` com `AllowOverride All` no `DocumentRoot` publicado;
2. habilitar `mod_headers` no Apache;
3. configurar `ServerTokens Prod` e manter `ServerSignature Off`;
4. validar a configuracao com `apache2ctl configtest` ou equivalente;
5. recarregar o Apache;
6. reenviar evidencias com `curl -I` dos dominios publicados para comprovacao dos headers.