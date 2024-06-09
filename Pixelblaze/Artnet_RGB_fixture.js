export var pixels = array(2)

var r,g,b
var bri, strobeTime, plIndex


export function beforeRender(delta) {
  
  // first 3 channels are color data
  var p = pixels[0]
  r = (p >> 8) & 0xff; g = p & 0xff; b = (p * 256 + .5) & 0xff  
  
  // next 3 channels are brightness, strobe, playlistIndex
  p = pixels[1]
  bri = (p >> 8) & 0xff; strobeTime = p & 0xff; plIndex = (p * 256 + .5) & 0xff  
  
  // scale control values as needed
  bri /= 255; strobeTime /= 255;
  
  var strobe = square(time(1 - strobeTime),0.3)
  
  // scale color values to [0..1] and set current brightness
  r = (r / 255) * bri; g = (g / 255) * bri; b = (b / 255) * bri
}

export function render(index) {

  rgb(r,r,b)
}