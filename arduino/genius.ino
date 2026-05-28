/*
  Projeto Genius - Leitura de 4 botões com envio serial.

  Montagem (usando INPUT_PULLUP):
  - botao_azul     no pino digital 2
  - botao_verde    no pino digital 3
  - botao_vermelho no pino digital 4
  - botao_amarelo  no pino digital 5
  - o outro terminal de cada botão vai para o GND

  Protocolo serial enviado ao computador (Django):
  BTN:azul
  BTN:verde
  BTN:vermelho
  BTN:amarelo
*/

const int BOTAO_AZUL_PIN = 2;
const int BOTAO_VERDE_PIN = 3;
const int BOTAO_VERMELHO_PIN = 4;
const int BOTAO_AMARELO_PIN = 5;

const unsigned long DEBOUNCE_MS = 40;

const int TOTAL_BOTOES = 4;
const int BUTTON_PINS[TOTAL_BOTOES] = {
  BOTAO_AZUL_PIN,
  BOTAO_VERDE_PIN,
  BOTAO_VERMELHO_PIN,
  BOTAO_AMARELO_PIN
};

const char* BUTTON_NAMES[TOTAL_BOTOES] = {
  "azul",
  "verde",
  "vermelho",
  "amarelo"
};

int lastReading[TOTAL_BOTOES];
int stableState[TOTAL_BOTOES];
unsigned long lastDebounceAt[TOTAL_BOTOES];

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < TOTAL_BOTOES; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    lastReading[i] = digitalRead(BUTTON_PINS[i]);
    stableState[i] = lastReading[i];
    lastDebounceAt[i] = 0;
  }
}

void loop() {
  for (int i = 0; i < TOTAL_BOTOES; i++) {
    handleButton(i);
  }
}

void handleButton(int index) {
  int pin = BUTTON_PINS[index];
  int reading = digitalRead(pin);

  if (reading != lastReading[index]) {
    lastDebounceAt[index] = millis();
    lastReading[index] = reading;
  }

  if ((millis() - lastDebounceAt[index]) > DEBOUNCE_MS) {
    if (reading != stableState[index]) {
      stableState[index] = reading;

      // INPUT_PULLUP: botão pressionado = LOW.
      if (stableState[index] == LOW) {
        Serial.print("BTN:");
        Serial.println(BUTTON_NAMES[index]);
      }
    }
  }
}

