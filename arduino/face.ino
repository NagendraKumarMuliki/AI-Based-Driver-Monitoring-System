#include <SoftwareSerial.h>
SoftwareSerial BT(10, 11);  // Bluetooth RX/TX

// LED pins
int ledActive = 2;
int ledBlink = 3;
int ledDrowsy = 4;
int ledYawn = 5;
int ledDistracted = 6;
int ledPhone = 7;

// Buzzer pin
int buzzerPin = 8;

// Reset button
int resetButton = 12;

// Matrix pins
#define SCL_Pin A5
#define SDA_Pin A4

// Face patterns
unsigned char face_active[16]     = {0x00,0x00,0x0e,0x6a,0x4e,0x40,0x40,0x50,0x50,0x40,0x40,0x4e,0x6a,0x0e,0x00,0x00};
unsigned char face_blink[16]      = {0x00,0x00,0x04,0x6e,0x44,0x40,0x40,0x50,0x50,0x40,0x40,0x44,0x6e,0x04,0x00,0x00};
unsigned char face_drowsy[16]     = {0x00,0x00,0x04,0x44,0x44,0x40,0x40,0x50,0x50,0x40,0x40,0x44,0x44,0x04,0x00,0x00};
unsigned char face_yawn[16]       = {0x00,0x00,0x04,0x02,0x04,0x40,0xa0,0xa8,0xa8,0xa0,0x40,0x04,0x02,0x04,0x00,0x00};
unsigned char face_distract[16]   = {0x00,0x00,0x00,0x0a,0x0a,0x04,0x00,0x00,0x10,0x40,0x40,0x4a,0x4a,0x04,0x00,0x00};
unsigned char face_phone[16]      = {0x00,0x84,0xe7,0xf5,0xf1,0xd9,0xaf,0xa9,0xa9,0xaf,0xd9,0xf1,0xf5,0xe7,0x84,0x00};

// State variables
char command = 'A';
char stableCommand = 'A';
unsigned long lastChangeTime = 0;
unsigned long lastStateTime = 0;

// Timers
const unsigned long stableDelay = 250;
const unsigned long minStateHold = 800;
unsigned long lastPing = 0;

// Counters
int countA = 0, countC = 0, countD = 0, countY = 0, countT = 0, countP = 0;

// Buzzer engine
int buzzerMode = 0;
int step = 0;
unsigned long timer = 0;

// Convert letter to full state name
String fullState(char c) {
  switch (c) {
    case 'A': return "ACTIVE";
    case 'C': return "BLINK";
    case 'D': return "DROWSY";
    case 'Y': return "YAWN";
    case 'T': return "DISTRACTED";
    case 'P': return "PHONE USAGE";
    default:  return "UNKNOWN";
  }
}

void setup() {
  Serial.begin(9600);
  BT.begin(9600);

  pinMode(ledActive, OUTPUT);
  pinMode(ledBlink, OUTPUT);
  pinMode(ledDrowsy, OUTPUT);
  pinMode(ledYawn, OUTPUT);
  pinMode(ledDistracted, OUTPUT);
  pinMode(ledPhone, OUTPUT);

  pinMode(buzzerPin, OUTPUT);
  pinMode(resetButton, INPUT_PULLUP);

  pinMode(SCL_Pin, OUTPUT);
  pinMode(SDA_Pin, OUTPUT);

  resetBuzzer();
  updateMatrixFace();
}

void loop() {
  unsigned long now = millis();

  // Read incoming command
  if (Serial.available() > 0) {
    char newCmd = Serial.read();
    if (newCmd != command) {
      command = newCmd;
      lastChangeTime = now;
    }
  }

  // Stabilize state
  if ((now - lastChangeTime >= stableDelay) && (now - lastStateTime >= minStateHold)) {
    if (stableCommand != command) {
      stableCommand = command;
      lastStateTime = now;

      resetBuzzer();
      updateMatrixFace();

      if (stableCommand == 'A') countA++;
      if (stableCommand == 'C') countC++;
      if (stableCommand == 'D') countD++;
      if (stableCommand == 'Y') countY++;
      if (stableCommand == 'T') countT++;
      if (stableCommand == 'P') countP++;

      BT.println(fullState(stableCommand));
    }
  }

  // Reset button
  if (digitalRead(resetButton) == LOW) {
    delay(200);
    sendSummary();
  }

  // Buzzer priority
  if (stableCommand == 'D')      buzzerMode = 1;
  else if (stableCommand == 'P') buzzerMode = 2;
  else if (stableCommand == 'T') buzzerMode = 3;
  else                           buzzerMode = 0;

  // LED control
  digitalWrite(ledActive,     stableCommand == 'A');
  digitalWrite(ledBlink,      stableCommand == 'C');
  digitalWrite(ledDrowsy,     stableCommand == 'D');
  digitalWrite(ledYawn,       stableCommand == 'Y');
  digitalWrite(ledDistracted, stableCommand == 'T');
  digitalWrite(ledPhone,      stableCommand == 'P');

  // Keep-alive (PING removed)
  if (now - lastPing >= 2000) {
    lastPing = now;
  }

  runBuzzer(now);
}

// Send summary counts
void sendSummary() {
  BT.println("===== SUMMARY =====");
  BT.print("ACTIVE: ");   BT.println(countA);
  BT.print("BLINK: ");    BT.println(countC);
  BT.print("DROWSY: ");   BT.println(countD);
  BT.print("YAWN: ");     BT.println(countY);
  BT.print("DISTRACT: "); BT.println(countT);
  BT.print("PHONE: ");    BT.println(countP);
  BT.println("===================");

  countA = countC = countD = countY = countT = countP = 0;
}

// Reset buzzer
void resetBuzzer() {
  noTone(buzzerPin);
  step = 0;
  timer = 0;
}

// Update matrix face
void updateMatrixFace() {
  switch (stableCommand) {
    case 'A': matrix_display(face_active); break;
    case 'C': matrix_display(face_blink); break;
    case 'D': matrix_display(face_drowsy); break;
    case 'Y': matrix_display(face_yawn); break;
    case 'T': matrix_display(face_distract); break;
    case 'P': matrix_display(face_phone); break;
    default:  matrix_display(face_active); break;
  }
}

// Buzzer patterns
void runBuzzer(unsigned long now) {
  switch (buzzerMode) {

    case 0:
      noTone(buzzerPin);
      step = 0;
      break;

    case 1:
      tone(buzzerPin, 3000);
      break;

    case 2:
      switch (step) {
        case 0: tone(buzzerPin, 3000); timer = now; step = 1; break;
        case 1: if (now - timer >= 120) { noTone(buzzerPin); timer = now; step = 2; } break;
        case 2: if (now - timer >= 120) { tone(buzzerPin, 3000); timer = now; step = 3; } break;
        case 3: if (now - timer >= 120) { noTone(buzzerPin); timer = now; step = 4; } break;
        case 4: if (now - timer >= 1000) step = 0; break;
      }
      break;

    case 3:
      switch (step) {
        case 0: tone(buzzerPin, 3000); timer = now; step = 1; break;
        case 1: if (now - timer >= 150) { noTone(buzzerPin); timer = now; step = 2; } break;
        case 2: if (now - timer >= 1000) step = 0; break;
      }
      break;
  }
}

// Matrix driver
void matrix_display(unsigned char matrix_value[]) {
  IIC_start();
  IIC_send(0xC0);
  for (int i = 0; i < 16; i++) IIC_send(matrix_value[i]);
  IIC_end();

  IIC_start();
  IIC_send(0x8A);
  IIC_end();
}

void IIC_start() {
  digitalWrite(SCL_Pin, HIGH);
  delayMicroseconds(3);
  digitalWrite(SDA_Pin, HIGH);
  delayMicroseconds(3);
  digitalWrite(SDA_Pin, LOW);
  delayMicroseconds(3);
}

void IIC_send(unsigned char send_data) {
  for (char i = 0; i < 8; i++) {
    digitalWrite(SCL_Pin, LOW);
    delayMicroseconds(3);
    digitalWrite(SDA_Pin, (send_data & 0x01) ? HIGH : LOW);
    delayMicroseconds(3);
    digitalWrite(SCL_Pin, HIGH);
    delayMicroseconds(3);
    send_data >>= 1;
  }
}

void IIC_end() {
  digitalWrite(SCL_Pin, LOW);
  delayMicroseconds(3);
  digitalWrite(SDA_Pin, LOW);
  delayMicroseconds(3);
  digitalWrite(SCL_Pin, HIGH);
  delayMicroseconds(3);
  digitalWrite(SDA_Pin, HIGH);
  delayMicroseconds(3);
}
