# Projeto Genius (Django + Arduino Serial)

## Requisitos
- Python 3.11+
- Arduino IDE
- Placa Arduino com 4 botoes

## Instalacao
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Banco e migracoes
```powershell
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate
```

## Executar servidor
```powershell
.\venv\Scripts\python.exe manage.py runserver
```

## Configuracao da serial
Por padrao o Django usa:
- porta: `COM3`
- baud rate: `9600`

Para alterar:
```powershell
$env:ARDUINO_SERIAL_PORT="COM5"
$env:ARDUINO_BAUD_RATE="9600"
.\venv\Scripts\python.exe manage.py runserver
```

## Fluxo
1. Tela mostra: clique em qualquer botao para iniciar.
2. Primeiro clique recebido do Arduino dispara contagem `3...2...1...`.
3. Sistema inicia rodada e sorteia sequencia de cores.
4. Usuario precisa repetir na ordem, com timeout por clique:
   - 1o clique: 5s
   - 2o clique: 4s
   - 3o clique: 3s
   - 4o em diante: minimo de 2s
5. Acerto de rodada soma +1 ponto.
6. Erro ou tempo esgotado mostra tela preta com "VOCE PERDEU" por 3s (ou ate o usuario clicar em qualquer botao), depois reinicia e grava tentativa no banco.

## Exibicao visual
- Contagem regressiva: tela preta com numero central.
- Sequencia sorteada: cada cor pisca por `0.75s`, com tela preta de `0.1s` entre cores.
- Timer superior na tela principal: fica oculto quando o fundo estiver preto.

## Protocolo serial esperado
Cada clique deve enviar uma linha:
- `BTN:azul`
- `BTN:verde`
- `BTN:vermelho`
- `BTN:amarelo`

Arquivo Arduino pronto em: `arduino/genius.ino`

## Teste manual sem Arduino
No navegador, use o teclado:
- `1` = azul
- `2` = verde
- `3` = vermelho
- `4` = amarelo

## Testes
```powershell
.\venv\Scripts\python.exe manage.py test
```
