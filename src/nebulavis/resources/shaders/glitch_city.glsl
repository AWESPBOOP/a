
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

float hash(vec2 p) {
return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
uv.y += sin(uTime * 0.5 + uv.x * 10.0) * 0.02 * bands[20];
float block = floor(uv.y * 20.0);
float glitch = hash(vec2(block, floor(uTime)));
vec3 base = vec3(0.1, 0.1, 0.15);
base += vec3(glitch * bands[30], bands[80] * 0.6, glitch * 0.3);
fragColor = vec4(base, 1.0);
}
