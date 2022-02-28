/* Pulse Generator to test AD2 Trigger/Timestamp recorder.
 * 
 * Version 2.0 - Output a fixed number of pulses when switch is activated
 *  - to test the trigger count/look for false triggers
 *
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
 * Doug Brantner 2/28/2022
 */

// TODO BUGS TO FIX IN FIRST VERSION:
// - subtract pulse width from TR, for more accurate pulse timing



// NOTE: for delayMicroseconds() - 
// Largest value that will produce an accurate delay is 16383
// 1 usec delay seems too small (~0.32usec on scope)
// 10 usec delay seems ok (slightly less than 10us but useable)

// TODO for LED to be visible we may need LED duration > Pulse Width...

long TR_DELAY = 2000;  // microseconds between pulses
// average expected ~2-4 milliseconds MRI TR (2000-4000 usec)

long PULSE_WIDTH = 10; // microseconds for high pulse
// NOTE: with this = 1, Rigol scope shows actual pulse with ~0.320 usec...


int N_PULSES = 1000;  // output a fixed number of pulses when momentary switch is closed
        

// TODO make these in the same block so we can just write both at once (bitwise/registerwise)
int TRIGGER_OUT_PIN = 8; // PORTB least significant bit 0000 0001
int LED_PIN = 13;  // PORTB  0010 0000
int START_SWITCH_PIN = 2; // momentary switch to start fixed count pulse train

// NOTE: BE CAREFUL WITH PORT B:
// PORTB maps to Arduino digital pins 8 to 13 The two high bits (6 & 7) map to the crystal pins and are not usable 
// TODO are they protected?

char PIN_8_ON  = B00000001;
char PIN_13_ON = B00100000;

char PIN_8_OFF = ~PIN_8_ON;

char LED_AND_TRIGGER_ON = PIN_8_ON | PIN_13_ON; // both on at the same time
      // this should look like 0010 0001
char LED_AND_TRIGGER_OFF = ~LED_AND_TRIGGER_ON; // both off; everything else ON
      // BE CAREFUL WITH HIGHEST 2 BITS!! see above.
      // this should look like 1101 1110


void setup() {
  // put your setup code here, to run once:

  pinMode(START_SWITCH_PIN, INPUT_PULLUP);
  pinMode(TRIGGER_OUT_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);


  digitalWrite(TRIGGER_OUT_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  // adjust TR delay for pulse width:
  TR_DELAY -= PULSE_WIDTH;
}

int pulses = 0; // how many pulses are emitted ('for' loop variable)

void loop() {
  // put your main code here, to run repeatedly:

  if (!digitalRead(START_SWITCH_PIN)) {
    // only checking once... hopefully we dont need to debounce beyond that...

    digitalWrite(LED_PIN, HIGH);  // turn on LED for full duration of pulses

    for (pulses = 0; pulses < N_PULSES; pulses++) {
      //PORTB = PORTB | LED_AND_TRIGGER_ON;
      PORTB = PORTB | PIN_8_ON; // only switch the signal pin; LED is on for the full duration now.

      delayMicroseconds(PULSE_WIDTH);

      //PORTB = PORTB & LED_AND_TRIGGER_OFF;
      PORTB = PORTB & PIN_8_OFF;

      delayMicroseconds(TR_DELAY);
    }

    digitalWrite(LED_PIN, LOW);
  }

}
