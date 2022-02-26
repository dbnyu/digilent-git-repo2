/* Pulse Generator to test AD2 Trigger/Timestamp recorder.
 * 
 * Generate a square pulse on one pin.
 * And additional synchronous LED pulse on separate pin.
 * 
 * Arduino 328 P clock speed = 16MHz
 * max speed ~16 instructions per microsecond
 * 
 * Direct Port Manipulation:
 * - https://www.arduino.cc/en/pmwiki.php?n=Reference/PortManipulation
 * - https://www.baldengineer.com/six-oscilloscope-measurements-using-arduino.html
 * 
 * Doug Brantner 2/25/2022
 */


// NOTE: for delayMicroseconds() - 
// Largest value that will produce an accurate delay is 16383

// TODO for LED to be visible we may need LED duration > Pulse Width...

long TR_DELAY = 2000;  // microseconds between pulses
// average expected ~2-4 milliseconds MRI TR (2000-4000 usec)

long PULSE_WIDTH = 1; // microseconds for high pulse
// NOTE: with this = 1, Rigol scope shows actual pulse with ~0.320 usec...
        

// TODO make these in the same block so we can just write both at once (bitwise/registerwise)
int TRIGGER_OUT_PIN = 8; // PORTB least significant bit 0000 0001
int LED_PIN = 13;  // PORTB  0010 0000

// NOTE: BE CAREFUL WITH PORT B:
// PORTB maps to Arduino digital pins 8 to 13 The two high bits (6 & 7) map to the crystal pins and are not usable 
// TODO are they protected?

char PIN_8_ON  = B00000001;
char PIN_13_ON = B00100000;

char LED_AND_TRIGGER_ON = PIN_8_ON | PIN_13_ON; // both on at the same time
      // this should look like 0010 0001
char LED_AND_TRIGGER_OFF = !LED_AND_TRIGGER_ON; // both off; everything else ON
      // BE CAREFUL WITH HIGHEST 2 BITS!! see above.
      // this should look like 1101 1110


void setup() {
  // put your setup code here, to run once:

  pinMode(TRIGGER_OUT_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // TODO pullups? add resistors on outputs?

  digitalWrite(TRIGGER_OUT_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

}

void loop() {
  // put your main code here, to run repeatedly:

  //digitalWrite(TRIGGER_OUT_PIN, HIGH);
  //digitalWrite(LED_PIN, HIGH);
  PORTB = PORTB | LED_AND_TRIGGER_ON;
  
  delayMicroseconds(PULSE_WIDTH);
  
  //digitalWrite(TRIGGER_OUT_PIN, LOW);
  //digitalWrite(LED_PIN, LOW);
  PORTB = PORTB & LED_AND_TRIGGER_OFF;

  delayMicroseconds(TR_DELAY);
}
