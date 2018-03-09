/*
  RSSI Antenna Tracker
*/

#include <Servo.h>
#include <Timer.h>

/*
 *  For testing different curves
 *  All new curves are more precise
 *  and maintain lock better than old RELATIVE
 *
 *  Uncomment one
 */
//#define EXPONENTIAL       // OK
//#define RELATIVE          // old, don't use
#define SIGMOID             // Best
//#define PROPORTIONAL      // twitchy

#define SIGMOID_SLOPE       1
#define SIGMOID_OFFSET      4

#if !defined(EXPONENTIAL) ^ !defined(SIGMOID) ^ !defined(PROPORTIONAL) ^ !defined(RELATIVE)
// all good
#else
  #error "Please define ONE tracking curve: EXPONENTIAL, SIGMOID, PROPORTIONAL, RELATIVE"
#endif


/*
   Pin mapping
   You can change these pins, just make sure that
   RSSI pins are analog inputs
   and servo pin supports PWM
*/
#define LEFT_RSSI_PIN       0     // analog RSSI measurement pin
#define RIGHT_RSSI_PIN      1
#define PAN_SERVO_PIN       5     // Pan servo pin

/*
   There is going to be some difference in receivers,
   one is going to be less sensitive than the other.
   It will result in slight offset when tracker is centered on target

   Find value that evens out RSSI
 */
#define RSSI_OFFSET_RIGHT   0
#define RSSI_OFFSET_LEFT    0

/*
   MIN and MAX RSSI values corresponding to 0% and 100% from receiver
   See serial monitor
*/
#define RSSI_MAX            400
#define RSSI_MIN            120

/*
   Safety limits for servo

   Find values where servo doesn't buzz at full deflection
*/
#define SERVO_MAX           180
#define SERVO_MIN           0

/*
 * Servo 'speed' limits
 * MAX and MIN step in degrees
 */
#define SERVO_MAX_STEP      5
#define SERVO_MIN_STEP      0.09     // prevents windup and servo crawl

/*
   Center deadband value!
   Prevents tracker from oscillating when target is in the center
   When using SIGMOID or EXPONENTIAL you can set this almost to 0
*/
#define DEADBAND            5

/*
   Depending which way around you put your servo
   you may have to change direction

   either 1 or -1
*/
#define SERVO_DIRECTION     1

#define FIR_SIZE            10
#define LAST                FIR_SIZE - 1


uint16_t rssi_left_array[FIR_SIZE];
uint16_t rssi_right_array[FIR_SIZE];


Timer timer;
Servo servoPan;

struct State {
  float anglePan;
  uint16_t avgLeft;
  uint16_t avgRight;
};

State state;

void setup() {
  servoPan.attach(PAN_SERVO_PIN);
  servoPan.write(90);

  state = {
    .anglePan = 90.0
  };

  // wipe array
  for (int i = 0; i < FIR_SIZE; i++) {
    rssi_right_array[i] = 0;
    rssi_left_array[i] = 0;
  }

  Serial.begin(115200);
  timer.every(50, mainLoop);
  timer.every(5, measureRSSI);
}


void loop() {

  timer.update();

}


void mainLoop() {

  state.avgLeft = max(avg(rssi_left_array, FIR_SIZE) + RSSI_OFFSET_LEFT, RSSI_MIN);
  state.avgRight = max(avg(rssi_right_array, FIR_SIZE) + RSSI_OFFSET_RIGHT, RSSI_MIN);

//  If avg RSSI is above 90%, don't move
//  if ((avgRight + avgLeft) / 2 > 360) {
//    return;
//  }

  /*
     the lower total RSSI is, the lower deadband gets
     allows more precise tracking when target is far away
  */
  uint8_t dynamicDeadband = (float(state.avgRight + state.avgLeft) / 2 - RSSI_MIN) / (RSSI_MAX - RSSI_MIN) * DEADBAND;

  // if target is in the middle, don't move
  if (abs(state.avgRight - state.avgLeft) < dynamicDeadband ) {
    return;
  }

  float ang = 0;

  // move towards stronger signal
  if (state.avgRight > state.avgLeft) {

  #if defined(EXPONENTIAL)
    float x = float(state.avgRight - state.avgLeft);
    x = x * x / 500;
    ang = x * SERVO_DIRECTION * -1;
  #endif

  #if defined(RELATIVE)
    ang = float(state.avgRight / state.avgLeft) * (SERVO_DIRECTION * -1);
  #endif

  #if defined(SIGMOID)
    float x = float(state.avgRight - state.avgLeft) / 10;
    x = SERVO_MAX_STEP / (1+ exp(-SIGMOID_SLOPE * x + SIGMOID_OFFSET));
    ang = x * SERVO_DIRECTION * -1;
  #endif

  #if defined(PROPORTIONAL)
    float x = float(state.avgRight - state.avgLeft) / 10;
    ang = x * SERVO_DIRECTION * -1;
  #endif
  }
  else {

  #if defined(EXPONENTIAL)
    float x = float(state.avgLeft - state.avgRight);
    x = x * x / 500;
    ang = x * SERVO_DIRECTION;
  #endif

  #if defined(RELATIVE)
    ang = float(state.avgLeft / state.avgRight) * SERVO_DIRECTION;
  #endif

  #if defined(SIGMOID)
    float x = float(state.avgLeft - state.avgRight) / 10;
    x = SERVO_MAX_STEP / (1+ exp(-SIGMOID_SLOPE * x + SIGMOID_OFFSET));
    ang = x * SERVO_DIRECTION;
  #endif

  #if defined(PROPORTIONAL)
    float x = float(state.avgLeft - state.avgRight) / 10;
    ang = x * SERVO_DIRECTION;
  #endif
  }

  // upper and lower limit for angle step
  ang = (abs(ang) > SERVO_MAX_STEP ? SERVO_MAX_STEP * ang/abs(ang) : ang);
  ang = (abs(ang) < SERVO_MIN_STEP ? 0 : ang);

  // move servo by n degrees
  movePanBy(ang);
  sendStatus();
}

uint8_t crc(const uint8_t* buf, size_t len)
{
  uint8_t res = 0;
  for(size_t i=0; i < len; ++i)
  {
    res += buf[i];
  }
  return res;
}

void sendStatus()
{
  struct StatusMessage {
    unsigned long timestamp;
    State state;
  };
  StatusMessage status;
  status.timestamp = millis();
  status.state = state;
  Serial.write('{');
  Serial.write((const uint8_t*)&status, sizeof(StatusMessage));
  Serial.write(crc((const uint8_t*)&status, sizeof(StatusMessage)));
  Serial.write('}');
}

void movePanBy(float angle) {

  state.anglePan += angle;
  state.anglePan = limit(SERVO_MIN, SERVO_MAX, state.anglePan);
  servoPan.write(state.anglePan);
}

void measureRSSI() {

  advanceArray(rssi_left_array, FIR_SIZE);
  advanceArray(rssi_right_array, FIR_SIZE);

  rssi_left_array[LAST] = analogRead(LEFT_RSSI_PIN);
  rssi_right_array[LAST] = analogRead(RIGHT_RSSI_PIN);
}

uint16_t avg(uint16_t samples[], uint8_t n) {

  uint32_t summ = 0;
  for (uint8_t i = 0; i < n; i++) {
    summ += samples[i];
  }

  return uint16_t(summ / n);
}

void advanceArray(uint16_t *samples, uint8_t n) {

  for (uint8_t i = 0; i < n - 1; i++) {
    samples[i] = samples[i + 1];
  }
}


float limit(float lowerLimit, float upperLimit, float var) {

  return min(max(var, lowerLimit), upperLimit);
}
