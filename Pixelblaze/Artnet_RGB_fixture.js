// Custom RGB fixture for use with Flamecaster Art-Net to Pixelblaze router
// Requires 3 DMX channels for full color control:
// 1 - Red
// 2 - Green
// 3 - Blue
export var channels = array(3)

var r,g,b
export function beforeRender(delta) {
  
  // first 3 channels are color data
  r = channels[0] / 255
  g = channels[1] / 255
  b = channels[2] / 255
}

export function render(index) {
  rgb(r,g,b)
}