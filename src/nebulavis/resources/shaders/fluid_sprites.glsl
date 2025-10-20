
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

float fbm(vec2 p) {
float v = 0.0;
float a = 0.5;
for (int i = 0; i < 5; ++i) {
v += a * sin(p.x) * cos(p.y);
p *= 2.1;
a *= 0.5;
}
return v;
}

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
vec2 p = uv * 3.0 + vec2(uTime * 0.2, -uTime * 0.15);
float field = fbm(p + bands[120]);
vec3 color = vec3(0.2 + field * 0.3, 0.3 + bands[110] * 0.5, 0.8 * field);
fragColor = vec4(color, 0.9);
}
