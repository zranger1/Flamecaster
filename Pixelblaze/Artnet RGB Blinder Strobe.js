// Custom RGB fixture with with white strobe "Blinder" section
// in the middle.  Requires 5 DMX channels for full control:
// 1 - Red
// 2 - Green
// 3 - Blue
// 4 - Strobe brightness
// 5 - Strobe speed (0 = off/on according to brightness)
//
// For use with Flamecaster Art-Net to Pixelblaze router

export var channels = array(5)
channels[0] = 0.75 * 255
channels[3] = 127
channels[4] = 0

var r,g,b
export var strobeBri, strobeRate,s

translate(-0.5,-0.5)

export function beforeRender(delta) {
  
  // first 3 channels are color data
  r = channels[0] / 255
  g = channels[1] / 255
  b = channels[2] / 255
  
  // next two channels are strobe brightness and rate
  // strobe rate controllable from 10hz to 1hz
  // rate == 0, is "on" (at specified brightness)
  strobeBri = channels[3] / 255
  strobeRate = (strobeRate == 0) ? 0 : mix(0.0015,0.015,channels[4] / 255)
  strobeBri = channels[3] / 255  
  strobeBri *= square(time(channels[4] / 255),0.1)   
}

export function render(index) {
  pct = index / pixelCount;
  
  if (abs(pct - 0.5) < 0.125) {
    hsv(0,0,strobeBri);
    return
  }  
  rgb(r,g,b)
}

export function render2D(index,x,y) {

  if (abs(y) < 0.125) {
    hsv(0,0,strobeBri);
    return
  }
  rgb(r,g,b)
}