
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
float x = uv.x * 10.0;
float y = uv.y * 6.0 + uTime * 0.4;
float h = abs(fract(x) - 0.5) < 0.02 || abs(fract(y) - 0.5) < 0.02 ? 1.0 : 0.0;
float bass = bands[8] * 2.0;
vec3 color = mix(vec3(0.05, 0.08, 0.12), vec3(0.3 + bass, 0.8, 0.6), h);
fragColor = vec4(color, 1.0);
}
