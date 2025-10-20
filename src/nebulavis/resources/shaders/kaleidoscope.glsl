
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0) - 0.5;
float angle = atan(uv.y, uv.x);
float radius = length(uv);
float segments = 8.0;
angle = mod(angle, 6.28318 / segments);
float wave = sin(radius * 15.0 - uTime * (1.0 + bands[40])) * 0.5 + 0.5;
vec3 color = vec3(wave * bands[10] + 0.2, wave * 0.5, 0.8 - wave * 0.3);
fragColor = vec4(color, 1.0);
}
